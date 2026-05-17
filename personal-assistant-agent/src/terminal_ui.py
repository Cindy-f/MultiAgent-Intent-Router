class Colors:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def cyan_bold(cls, text: str) -> str:
        return f"{cls.CYAN}{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.RESET}"

    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.RESET}"

    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.RESET}"

    @classmethod
    def red_bold(cls, text: str) -> str:
        return f"{cls.RED}{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def dim(cls, text: str) -> str:
        return f"{cls.DIM}{text}{cls.RESET}"

    @classmethod
    def white(cls, text: str) -> str:
        return f"{text}{cls.RESET}"


def print_table(headers: list[str], rows: list[list[str]], col_widths: list[int]) -> None:
    border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    print(border)
    print(
        "|"
        + "|".join(
            f" {Colors.BOLD}{headers[i]:<{col_widths[i]}}{Colors.RESET} "
            for i in range(len(headers))
        )
        + "|"
    )
    print(border)
    for row in rows:
        print(
            "|"
            + "|".join(f" {row[i]:<{col_widths[i]}} " for i in range(len(row)))
            + "|"
        )
    print(border)
