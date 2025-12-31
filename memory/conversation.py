from typing import List, Dict
import time

class ConversationMemory:
    """Manages simple in-memory conversation storage"""
    
    def __init__(self, max_history: int = 10):
        self.history = {}
        self.max_history = max_history

    def get_history(self, session_id: str) -> List[Dict]:
        return self.history.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.history:
            self.history[session_id] = []
        
        self.history[session_id].append({
            "role": role, 
            "content": content,
            "timestamp": time.time()
        })
        
        # Trim
        if len(self.history[session_id]) > self.max_history:
            self.history[session_id] = self.history[session_id][-self.max_history:]

    def clear(self, session_id: str):
        if session_id in self.history:
            del self.history[session_id]
