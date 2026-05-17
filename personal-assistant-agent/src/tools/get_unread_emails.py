from typing import Any, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def get_unread_emails(auth: Credentials, max_results: int) -> List[dict[str, Any]]:
    gmail = build("gmail", "v1", credentials=auth)

    response = (
        gmail.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=max_results)
        .execute()
    )

    messages = response.get("messages") or []
    emails: List[dict[str, Any]] = []

    for message in messages:
        if not message or not message.get("id"):
            continue
        email_response = (
            gmail.users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )
        headers = (email_response.get("payload") or {}).get("headers") or []

        def get_header(name: str) -> str:
            for h in headers:
                if (h.get("name") or "").lower() == name.lower():
                    return h.get("value") or "Unknown"
            return "Unknown"

        emails.append(
            {
                "id": email_response.get("id"),
                "from": get_header("From"),
                "subject": get_header("Subject"),
                "date": get_header("Date"),
                "snippet": email_response.get("snippet"),
            }
        )

    return emails
