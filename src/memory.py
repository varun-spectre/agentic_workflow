from typing import List, Dict

class Memory:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add(self, role: str, message: str):
        """
        Add a memory step.
        `role` could be: system / user / agent / tool / etc.
        """
        self.history.append({"role": role, "message": message})

    def get_context(self) -> str:
        """Returns the entire conversation context as a string"""
        return "\n".join([f"{step['role']}: {step['message']}" for step in self.history])

    def get_last(self, n: int = 1) -> List[Dict[str, str]]:
        """Returns the last `n` messages"""
        return self.history[-n:]

# TODO: Future improvements
# - Implement token-limited memory
# - Add step filtering (e.g., only last plan+execution)
# - Add long-term memory storage options:
#   - File persistence
#   - Redis integration
#   - Vector DB support

