import sys

from dotenv import load_dotenv

load_dotenv()

from src.cli import Colors, print_table
from src.coordinator import LlmCoordinator
from src.dates import local_iso_date


def main() -> None:
    coordinator = LlmCoordinator()

    try:
        coordinator.authenticate()
        print("\033[2J\033[H", end="")
        print(Colors.cyan_bold("      🤖 PERSONAL ASSISTANT AGENT METRICS MAIN        "))

        print(Colors.yellow("📥 UNREAD INBOX HIGHLIGHTS"))
        unread_emails = coordinator.email.check_unread_emails()
        rows = [
            [email["from"][:28], email["subject"][:48]]
            for email in unread_emails
        ]
        print_table(["From", "Subject"], rows, [30, 50])

        print(Colors.green("\n📅 TODAY'S TIMELINE SCHEDULE"))
        daily_schedule = coordinator.calendar.fetch_daily_meeting_schedule(local_iso_date())

        if not daily_schedule.events:
            print(Colors.dim("   No events scheduled for today."))
        else:
            for event in daily_schedule.events:
                print(
                    f"   ⏱️  {Colors.BOLD}{event.time_window}{Colors.RESET} ➡️ {event.summary}"
                )

        clock = coordinator.time.get_current_time()
        print(Colors.dim(f"\n📊 Local time ({clock['timezone']}): {clock['display']}"))
        print(Colors.cyan_bold("======================================================\n"))

    except Exception as error:
        print(Colors.red_bold(f"Error during dashboard execution: {error}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
