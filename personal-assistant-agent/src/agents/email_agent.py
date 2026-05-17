from typing import Any, List

from src.agents.base import BaseAgent
from src.tools.get_unread_emails import get_unread_emails


class EmailAgent(BaseAgent):
    def check_unread_emails(self, max_results: int = 10) -> List[dict[str, Any]]:
        if not self.google.oauth2_client:
            raise RuntimeError("Google client not authenticated")
        return get_unread_emails(self.google.oauth2_client, max_results)
