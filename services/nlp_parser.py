import re
import os
import json
from datetime import datetime, timedelta

# Keyword mappings for categories (English + Hindi + Hinglish)
CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "dinner", "lunch", "breakfast", "food", "khana", "nashta", "chai", "coffee", "tea",
        "pizza", "burger", "biryani", "samosa", "mithai", "momos", "maggi", "dominos",
        "zomato", "swiggy", "mcdonalds", "starbucks", "subway", "kfc", "restaurant",
        "dhaba", "cafe", "hotel", "snack", "snacks", "groceries", "grocery", "rashan",
        "drinks", "beer", "pub", "bar", "buffet", "meal", "eating", "eat", "party",
        "daaru", "paneer", "roti", "sabzi", "roll", "dosa", "idli"
    ],
    "Travel & Cab": [
        "uber", "ola", "rapido", "cab", "taxi", "auto", "metro", "bus", "train", "flight",
        "plane", "railway", "ticket", "tickets", "petrol", "diesel", "fuel", "toll",
        "parking", "ride", "travel", "commute", "kiraya", "bhada", "rikshaw", "gaadi",
        "scooter", "bike", "trip", "safar", "indrive", "blablacar"
    ],
    "Bills & Utilities": [
        "electricity", "electric", "power", "bijli", "water", "pani", "wifi", "wi-fi",
        "internet", "broadband", "recharge", "phone recharge", "mobile", "gas", "cylinder",
        "rent", "kiraya", "room rent", "kamre ka rent", "makaan malik", "maintenance",
        "maid", "kaamwali", "cook", "bill", "bills", "utility", "utilities", "broadband"
    ],
    "Shopping": [
        "shopping", "amazon", "flipkart", "myntra", "meesho", "zara", "h&m", "clothes",
        "kapde", "shirt", "pants", "shoes", "joote", "sneakers", "mall", "electronics",
        "gadget", "laptop", "mobile phone", "samaan", "khareeda", "bought", "purchase"
    ],
    "Subscriptions": [
        "netflix", "spotify", "youtube", "youtube premium", "prime", "amazon prime",
        "hotstar", "disney", "apple", "icloud", "chatgpt", "subscription", "membership"
    ],
    "Entertainment": [
        "movie", "film", "cinema", "pvr", "inox", "concert", "show", "event", "game",
        "gaming", "steam", "playstation", "outing", "ghumna", "amusement"
    ],
    "Health": [
        "medicine", "dawai", "pharmacy", "chemist", "doctor", "hospital", "clinic",
        "consultation", "test", "lab", "gym", "protein", "fitness", "yoga", "ilaaj"
    ]
}

PAYMENT_MODES = {
    "UPI": ["upi", "gpay", "google pay", "phonepe", "paytm", "bhim", "qr", "scan"],
    "Cash": ["cash", "nakad", "rokhda", "cash se", "cash diya", "cod"],
    "Card": ["card", "credit card", "debit card", "visa", "mastercard", "rupay", "swipe"],
    "Online": ["online", "netbanking", "transfer", "neft", "imps", "rtgs", "bank transfer"]
}

def parse_amount(text):
    """Extract numeric amount from text supporting ₹, Rs, INR, bucks, etc."""
    # Pattern 1: ₹500 or Rs. 500 or INR 500
    match = re.search(r'(?:₹|rs\.?|inr|rupees?|rupaye?|rupay)\s*([0-9]+(?:\.[0-9]{1,2})?)', text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Pattern 2: 500 ₹ or 500 rs or 500 bucks
    match = re.search(r'([0-9]+(?:\.[0-9]{1,2})?)\s*(?:₹|rs\.?|inr|rupees?|rupaye?|rupay|bucks?)', text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Pattern 3: Standalone numbers (ignoring common years like 2024, 2025, 2026 or percentages)
    matches = re.findall(r'\b([0-9]+(?:\.[0-9]{1,2})?)\b', text)
    for m in matches:
        val = float(m)
        if val in [2024, 2025, 2026, 2027]:
            continue
        if 0 < val < 10000000:
            return val

    return 0.0

def parse_category(text):
    """Detect category from text keywords (English, Hindi, Hinglish)"""
    lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower):
                return cat
    return "Food & Dining" if any(w in lower for w in ["khana", "dinner", "lunch", "food", "nashta"]) else "General"

def parse_payment_mode(text):
    """Detect payment mode (UPI, Cash, Card, Online)"""
    lower = text.lower()
    for mode, keywords in PAYMENT_MODES.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower):
                return mode
    return "UPI"

def parse_date(text):
    """Detect date references like yesterday/kal, today/aaj, parso"""
    lower = text.lower()
    today = datetime.now()

    if any(w in lower for w in ["yesterday", "kal", "beeta kal"]):
        target = today - timedelta(days=1)
        return target.strftime("%Y-%m-%d")
    elif "parso" in lower:
        target = today - timedelta(days=2)
        return target.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")

def parse_split(text, total_amount):
    """Detect split intent, names, and user's calculated share"""
    lower = text.lower()
    
    # Check if split keywords exist
    split_indicators = [
        "split", "share", "shared", "divide", "aadha", "aadha aadha", "half", "half half",
        "50-50", "50%", "barabar", "hissa", "baata", "divide kiya", "contri"
    ]
    is_split = any(re.search(r'\b' + re.escape(ind) + r'\b', lower) for ind in split_indicators)

    # Names extraction
    names = []
    
    # Hinglish pattern: "... [Name] ke saath" or "[Name] aur [Name] ke saath"
    ke_saath_match = re.search(r'([A-Za-z]+(?:\s*(?:,|aur|and)\s*[A-Za-z]+)*)\s+ke\s+saath', text, re.IGNORECASE)
    if ke_saath_match:
        is_split = True
        raw_names = ke_saath_match.group(1)
        names = [n.strip().title() for n in re.split(r'\s*(?:,|aur|and)\s*', raw_names) if n.strip().lower() not in ["dost", "bhai", "sab", "roommate"]]

    # English pattern: "with [Name]" or "split with [Name]"
    if not names:
        with_match = re.search(r'(?:split\s+with|with)\s+([A-Za-z]+(?:\s*(?:,|and|aur)\s*[A-Za-z]+)*)', text, re.IGNORECASE)
        if with_match:
            is_split = True
            raw_names = with_match.group(1)
            names = [n.strip().title() for n in re.split(r'\s*(?:,|and|aur)\s*', raw_names) if n.strip().lower() not in ["upi", "cash", "card", "me", "friend", "friends", "bro"]]

    if is_split:
        expense_type = "Split"
        split_with = ", ".join(names) if names else "Friend"
        num_people = len(names) + 1 if names else 2
        user_amount = round(total_amount / float(num_people), 2)
        split_type = "Equal"
    else:
        expense_type = "Personal"
        split_with = ""
        user_amount = total_amount
        split_type = "Equal"

    return expense_type, split_with, split_type, user_amount

def clean_description(text, category):
    """Generate a clean, readable description from natural text"""
    clean = re.sub(r'(?:₹|rs\.?|inr)\s*[0-9]+(?:\.[0-9]+)?', '', text, flags=re.IGNORECASE)
    clean = re.sub(r'\b[0-9]+(?:\.[0-9]+)?\s*(?:bucks?|rupaye?|rupay)?\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(?:via|by|with|se|ko|diya|bhara|liya|paid|spent|kharcha|split|equally|aadha|aadha aadha|half half|upi|cash|gpay|paytm|phonepe)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if len(clean) >= 3:
        return clean.capitalize()
    return f"{category} Expense"

def parse_with_llm(text):
    """Optional LLM adapter if GEMINI_API_KEY is configured"""
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not gemini_key:
        return None
    try:
        import urllib.request
        prompt = f"""Extract expense details from this message in JSON format. The message may be in English, Hindi, or Hinglish:
Text: "{text}"
Today is {datetime.now().strftime("%Y-%m-%d")}.
Return ONLY valid JSON matching this schema:
{{
  "amount": <float user net share>,
  "total_bill_amount": <float total bill amount>,
  "category": "Food & Dining" | "Travel & Cab" | "Shopping" | "Bills & Utilities" | "Entertainment" | "Health" | "Subscriptions" | "General",
  "expense_type": "Personal" | "Split",
  "split_with": "<string comma-separated names if split, else empty>",
  "split_type": "Equal",
  "payment_mode": "UPI" | "Cash" | "Card" | "Online",
  "date": "YYYY-MM-DD",
  "description": "<clean short title>"
}}"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=4) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            parsed_text = res_body["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(parsed_text)
            data["original_text"] = text
            return data
    except Exception as e:
        print(f"⚠️ LLM adapter notice: {e}. Falling back to instant local NLP engine.")
        return None

def parse_natural_language_expense(text):
    """Main parsing pipeline with Hybrid LLM + English, Hindi, and Hinglish understanding"""
    raw_text = text.strip()

    # Try LLM if API key is configured
    llm_result = parse_with_llm(raw_text)
    if llm_result and llm_result.get("total_bill_amount", 0) > 0:
        return llm_result

    # Instant zero-latency rule-based local parser
    total_amount = parse_amount(raw_text)
    category = parse_category(raw_text)
    payment_mode = parse_payment_mode(raw_text)
    date_str = parse_date(raw_text)
    expense_type, split_with, split_type, user_amount = parse_split(raw_text, total_amount)
    description = clean_description(raw_text, category)

    return {
        "amount": user_amount,
        "total_bill_amount": total_amount,
        "category": category,
        "expense_type": expense_type,
        "split_with": split_with,
        "split_type": split_type,
        "payment_mode": payment_mode,
        "date": date_str,
        "description": description,
        "original_text": raw_text
    }
