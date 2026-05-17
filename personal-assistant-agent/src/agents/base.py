from src.services.google_services_utils import GoogleServicesUtils


class BaseAgent:
    def __init__(self, google: GoogleServicesUtils) -> None:
        self.google = google
