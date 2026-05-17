from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Email:
    id: str
    subject: str
    sender: str
    received_date: datetime
    is_read: bool


@dataclass
class Meeting:
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    attendees: List[str]


@dataclass
class Token:
    access_token: str
    refresh_token: str
    expiry_date: datetime
