import json
from typing import Any, Callable, Optional, Union

import questionary
import typer
import yaml


class ExitWithMessage(typer.Exit):
    def __init__(self, message=None, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)


def as_code(text: str) -> str:
    """Returns the given text colored and in backticks."""
    return typer.style(f"`{text}`", fg=typer.colors.CYAN)


def red(text: str) -> str:
    return typer.style(text, fg=typer.colors.RED)


def blue(text: str) -> str:
    return typer.style(text, fg=typer.colors.BLUE)


def yellow(text: str) -> str:
    return typer.style(text, fg=typer.colors.YELLOW)


def green(text: str) -> str:
    return typer.style(text, fg=typer.colors.GREEN)


def warn(message: str) -> None:
    """Prints a warning message."""
    print(f"{yellow('Warning:')} {message}")


def error(message: str, code: int = 1) -> Exception:
    """Prints an error message and returns an exception."""
    print(f"{red('Error:')} {message}")
    return ExitWithMessage(message=message, code=code)


def censor_token(token: str) -> str:
    return ("*" * (len(token) - 6)) + token[-6:]


def list_input(
    prompt: str,
    choices: list[Any],
    default: Optional[Union[str, questionary.Choice, dict[str, Any]]] = None,
) -> str:
    """Presents the user with a list of choices that can be navigated with
    the up and down arrows.
    """
    return questionary.select(prompt, choices=choices, default=default).unsafe_ask()


def choice(value: Any, name: str) -> Any:
    return questionary.Choice(title=name, value=value)


def input(prompt: str, default: str = "", validate: Optional[Callable] = None) -> str:  # noqa: A001
    """Prompts the user for text input."""
    return questionary.text(prompt, default=default, validate=validate).unsafe_ask()


def password_input(prompt: str, default: str = "") -> str:
    """Prompts the user for text input, hidden by dots."""
    return questionary.password(prompt, default=default).unsafe_ask()


def print(*args, **kwargs):  # noqa: A001
    """Echos text to the console."""
    return typer.echo(*args, **kwargs)


def print_json(data: Any):
    return typer.echo(json.dumps(data, indent=2))


def print_yaml(data: Any):
    return typer.echo(yaml.dump(data))


def erase_previous_line(number_of_lines: int = 1) -> None:
    """Erases the previous line of output, which can then be printed over."""
    return typer.echo("\033[F\033[K" * number_of_lines + "\033[F")


def confirm(prompt: str, default: bool = True) -> bool:
    """Asks the user to respond yes or no to the prompt."""
    return questionary.confirm(prompt, default=default).unsafe_ask()


def bool_input(prompt: str, default: bool = False) -> bool:
    return confirm(prompt, default=default)
