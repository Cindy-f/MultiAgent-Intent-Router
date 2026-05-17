import sys

from dotenv import load_dotenv

load_dotenv()

from src.cli import Colors
from src.coordinator import LlmCoordinator


def main() -> None:
    coordinator = LlmCoordinator()

    try:
        print(Colors.cyan_bold("Authenticating with Google..."))
        coordinator.authenticate()
        print("\033[2J\033[H", end="")
        print(Colors.cyan_bold("Personal Assistant (Supervisor + specialists)"))
        print(Colors.dim(f"LLM: {coordinator.llm_label}"))
        print(
            Colors.dim(
                "Ask about unread email, your calendar, or the time. Type 'exit' to quit.\n"
            )
        )

        while True:
            try:
                user_input = input(Colors.yellow("You: ")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue
            if user_input.lower() == "exit":
                break

            try:
                print(Colors.dim("Thinking..."), end="\r", flush=True)
                reply = coordinator.chat(user_input)
                print("\033[K", end="")
                print(f"{Colors.green('Assistant:')} {reply}\n")
            except Exception as error:
                print("\033[K", end="")
                print(f"{Colors.red('Error:')} {error}\n")

    except Exception as error:
        print(Colors.red_bold(f"Failed to start assistant: {error}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
