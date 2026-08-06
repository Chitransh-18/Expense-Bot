import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials

from config import SPREADSHEET_NAME, GOOGLE_CREDENTIALS, OWNER_EMAIL, logger
from services.cache_service import cache_service

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class SheetsService:
    def __init__(self):
        self.gc: Optional[gspread.Client] = None
        self.worksheet_expenses: Optional[gspread.Worksheet] = None
        self.worksheet_history: Optional[gspread.Worksheet] = None

    def setup(self) -> Optional[str]:
        """Initialize Google Sheets connection with modern service account authentication"""
        try:
            if not GOOGLE_CREDENTIALS:
                logger.error("GOOGLE_CREDENTIALS environment variable not set.")
                return None

            creds_dict = json.loads(GOOGLE_CREDENTIALS)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            self.gc = gspread.authorize(creds)

            try:
                spreadsheet = self.gc.open(SPREADSHEET_NAME)
                logger.info(f"Opened existing spreadsheet: {SPREADSHEET_NAME}")
            except gspread.SpreadsheetNotFound:
                spreadsheet = self.gc.create(SPREADSHEET_NAME)
                if OWNER_EMAIL:
                    spreadsheet.share(OWNER_EMAIL, perm_type='user', role='writer')
                logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")

            try:
                self.worksheet_expenses = spreadsheet.worksheet("Expenses")
            except gspread.WorksheetNotFound:
                self.worksheet_expenses = spreadsheet.add_worksheet("Expenses", rows=1000, cols=16)
                self.worksheet_expenses.append_row([
                    "Transaction ID", "Timestamp", "User ID", "Username", "First Name",
                    "Expense Type", "Category", "Amount", "Payment Mode", "Description", "Date", "Status", "Notes", 
                    "Split With", "Split Type", "Split Details"
                ])
                logger.info("Created Expenses worksheet")

            try:
                self.worksheet_history = spreadsheet.worksheet("Chat_History")
            except gspread.WorksheetNotFound:
                self.worksheet_history = spreadsheet.add_worksheet("Chat_History", rows=5000, cols=10)
                self.worksheet_history.append_row([
                    "Timestamp", "User ID", "Username", "First Name",
                    "Action Type", "Action Details", "Message Text", "Button Clicked", "Chat ID", "Message ID"
                ])
                logger.info("Created Chat History worksheet")

            logger.info(f"Connected to Google Sheets: {spreadsheet.url}")
            return spreadsheet.url

        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}", exc_info=True)
            return None

    async def log_chat_history_async(
        self, user_id: int, username: str, first_name: str, action_type: str,
        action_details: str, message_text: str = "", button_clicked: str = "",
        chat_id: str = "", message_id: str = ""
    ) -> bool:
        """Log interactions asynchronously"""
        if not self.worksheet_history:
            return False
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [
                timestamp, str(user_id), username or "N/A", first_name or "N/A",
                action_type, action_details, message_text[:200] if message_text else "",
                button_clicked, str(chat_id), str(message_id)
            ]
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.worksheet_history.append_row, row)
            return True
        except Exception as e:
            logger.error(f"Error logging chat history: {e}")
            return False

    async def save_expense_async(
        self, user_id: int, username: str, first_name: str, expense_type: str,
        category: str, amount: float, payment_mode: str, description: str = "",
        split_with: Optional[List[str]] = None, split_type: Optional[str] = None,
        split_details: Optional[Any] = None
    ) -> Optional[str]:
        """Save expense asynchronously and invalidate user cache"""
        if not self.worksheet_expenses:
            return None
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date = datetime.now().strftime("%Y-%m-%d")
            transaction_id = f"TXN{user_id}_{int(datetime.now().timestamp())}"

            split_with_str = ", ".join(split_with) if split_with else ""
            split_details_str = str(split_details) if split_details else ""

            row = [
                transaction_id, timestamp, str(user_id), username or "N/A", first_name or "N/A",
                expense_type, category, float(amount), payment_mode, description, date, "Completed", "",
                split_with_str, split_type or "", split_details_str
            ]

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.worksheet_expenses.append_row, row)

            # Invalidate user cache
            cache_service.invalidate_user_cache(str(user_id))

            await self.log_chat_history_async(
                user_id, username, first_name, "Expense Added",
                f"{expense_type} - {category} - ₹{amount} - {payment_mode}", description
            )
            return transaction_id
        except Exception as e:
            logger.error(f"Error saving expense: {e}", exc_info=True)
            return None

    async def delete_expense_async(self, user_id: int, transaction_id: str) -> bool:
        """Delete a transaction by Transaction ID"""
        if not self.worksheet_expenses:
            return False
        try:
            loop = asyncio.get_running_loop()
            all_records = await loop.run_in_executor(None, self.worksheet_expenses.get_all_records)
            
            # Row index in gspread is 2-indexed because line 1 is headers
            target_row = None
            for idx, record in enumerate(all_records, start=2):
                if str(record.get('Transaction ID', '')) == str(transaction_id) and str(record.get('User ID', '')) == str(user_id):
                    target_row = idx
                    break

            if target_row:
                await loop.run_in_executor(None, self.worksheet_expenses.delete_rows, target_row)
                cache_service.invalidate_user_cache(str(user_id))
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting expense {transaction_id}: {e}", exc_info=True)
            return False

    async def get_user_expenses_async(self, user_id: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get user's expenses with per-user caching"""
        uid = str(user_id)
        if not force_refresh:
            cached = cache_service.get_cached_expenses(uid)
            if cached is not None:
                return cached

        if not self.worksheet_expenses:
            return []

        try:
            loop = asyncio.get_running_loop()
            max_retries = 3
            all_records = []
            for attempt in range(max_retries):
                try:
                    all_records = await loop.run_in_executor(None, self.worksheet_expenses.get_all_records)
                    break
                except Exception as e:
                    logger.warning(f"Sheets fetch attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                    else:
                        raise

            user_expenses = [r for r in all_records if str(r.get('User ID', '')) == uid]
            cache_service.set_cached_expenses(uid, user_expenses)
            return user_expenses
        except Exception as e:
            logger.error(f"Error fetching expenses for user {user_id}: {e}", exc_info=True)
            return []

    async def get_user_chat_log_async(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's chat interaction history"""
        if not self.worksheet_history:
            return []
        try:
            loop = asyncio.get_running_loop()
            all_history = await loop.run_in_executor(None, self.worksheet_history.get_all_records)
            user_history = [r for r in all_history if str(r.get('User ID', '')) == str(user_id)]
            user_history.reverse()
            return user_history[:limit]
        except Exception as e:
            logger.error(f"Error fetching chat log: {e}")
            return []

sheets_service = SheetsService()
