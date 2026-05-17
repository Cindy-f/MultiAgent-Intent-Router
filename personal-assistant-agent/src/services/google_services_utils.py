import json
import os
from typing import Any, List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request


class GoogleServicesUtils:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.oauth2_client: Optional[Credentials] = None
        self._token_path = os.environ.get("TOKEN_PATH", "token.json")

    def _client_config(self) -> dict:
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }

    def _normalize_token(self, data: dict, scopes: List[str]) -> dict:
        """Support token.json from Python or from the old Node/googleapis format."""
        normalized = dict(data)
        if "token" not in normalized and "access_token" in normalized:
            normalized["token"] = normalized["access_token"]

        if not normalized.get("client_id") and self.client_id:
            normalized["client_id"] = self.client_id
        if not normalized.get("client_secret") and self.client_secret:
            normalized["client_secret"] = self.client_secret

        if not normalized.get("scopes"):
            scope_val = normalized.get("scope")
            if isinstance(scope_val, str):
                normalized["scopes"] = scope_val.split()
            else:
                normalized["scopes"] = scopes

        if not normalized.get("token_uri"):
            normalized["token_uri"] = "https://oauth2.googleapis.com/token"

        return normalized

    def authenticate(self, scopes: List[str]) -> None:
        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "Missing CLIENT_ID or CLIENT_SECRET in .env (required for Google OAuth)."
            )

        saved = self.load_token()
        if saved:
            self.oauth2_client = Credentials.from_authorized_user_info(
                self._normalize_token(saved, scopes), scopes
            )
            if self.oauth2_client.valid:
                print("Successfully authenticated using existing token.json")
                return
            if self.oauth2_client.expired and self.oauth2_client.refresh_token:
                self.oauth2_client.refresh(Request())
                self.save_token(self._credentials_to_dict(self.oauth2_client))
                print("Successfully authenticated using existing token.json")
                return

        print("No existing token found. Starting first-time authorization...")
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=scopes,
            redirect_uri=self.redirect_uri,
        )
        auth_url, _ = flow.authorization_url(access_type="offline")
        print("Authorize this app by visiting this url:\n", auth_url)
        code = input("Enter the authorization code from that page here: ").strip()
        try:
            flow.fetch_token(code=code)
            self.oauth2_client = flow.credentials
            self.save_token(self._credentials_to_dict(self.oauth2_client))
            print("Authentication successful! token.json saved.")
        except Exception as err:
            raise RuntimeError(f"Failed to retrieve access token from code: {err}") from err

    def save_token(self, token: Any) -> None:
        with open(self._token_path, "w", encoding="utf-8") as f:
            json.dump(token, f)

    def load_token(self) -> Optional[Any]:
        if os.path.exists(self._token_path):
            with open(self._token_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    @staticmethod
    def _credentials_to_dict(creds: Credentials) -> dict:
        return {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or []),
        }
