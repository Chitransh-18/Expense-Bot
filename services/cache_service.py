import time
from typing import Dict, List, Any, Optional

class UserCacheService:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._user_expenses: Dict[str, List[Dict[str, Any]]] = {}
        self._expenses_last_updated: Dict[str, float] = {}
        self._history_cache: Dict[str, List[Dict[str, Any]]] = {}

    def get_cached_expenses(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        uid = str(user_id)
        if uid in self._user_expenses and uid in self._expenses_last_updated:
            if time.time() - self._expenses_last_updated[uid] < self.ttl_seconds:
                return self._user_expenses[uid]
        return None

    def set_cached_expenses(self, user_id: str, expenses: List[Dict[str, Any]]):
        uid = str(user_id)
        self._user_expenses[uid] = expenses
        self._expenses_last_updated[uid] = time.time()

    def invalidate_user_cache(self, user_id: str):
        uid = str(user_id)
        self._user_expenses.pop(uid, None)
        self._expenses_last_updated.pop(uid, None)
        self._history_cache.pop(uid, None)

    def invalidate_all(self):
        self._user_expenses.clear()
        self._expenses_last_updated.clear()
        self._history_cache.clear()

cache_service = UserCacheService()
