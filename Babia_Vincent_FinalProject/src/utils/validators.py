"""
validators.py
-------------
Input validation and safe prompt helpers for the Finance Tracker CLI.

Every user-facing input passes through one of these functions so that business
logic is never handed malformed data.

Intermediate concepts demonstrated:
  - Decorators (retry_on_invalid)
  - Recursive / loop-based input loops
  - Exception handling (ValueError, KeyboardInterrupt)
  - Type coercion with explicit error messages
"""

from datetime import datetime
from typing import Any, Callable, Iterable, Optional, TypeVar

from src.utils.display import error, warning

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic safe-prompt helpers
# ---------------------------------------------------------------------------

def prompt(
    message: str,
    allow_empty: bool = False,
    default: Optional[str] = None,
) -> str:
    """
    Prompt the user for a non-empty string.

    Args:
        message: Prompt text shown to the user.
        allow_empty: If True, an empty response returns *default* (or '').
        default: Value returned on empty input when allow_empty is True.

    Returns:
        Stripped string input.
    """
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"  {message}{suffix}: ").strip()
        except KeyboardInterrupt:
            print()
            raise

        if value:
            return value
        if allow_empty:
            return default or ""
        error("Input cannot be empty. Please try again.")


def prompt_float(
    message: str,
    min_val: float = 0.01,
    max_val: float = 10_000_000.0,
) -> float:
    """
    Prompt the user for a positive float within [min_val, max_val].

    Args:
        message: Prompt text.
        min_val: Minimum acceptable value (inclusive).
        max_val: Maximum acceptable value (inclusive).

    Returns:
        Validated float.
    """
    while True:
        raw = prompt(message)
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            error(f"'{raw}' is not a valid number. Please enter digits only.")
            continue

        if value < min_val:
            error(f"Amount must be at least {min_val:.2f}.")
        elif value > max_val:
            error(f"Amount cannot exceed {max_val:,.2f}.")
        else:
            return round(value, 2)


def prompt_int(
    message: str,
    min_val: int = 1,
    max_val: int = 9_999,
) -> int:
    """
    Prompt the user for an integer within [min_val, max_val].

    Args:
        message: Prompt text.
        min_val: Minimum acceptable value (inclusive).
        max_val: Maximum acceptable value (inclusive).

    Returns:
        Validated integer.
    """
    while True:
        raw = prompt(message)
        try:
            value = int(raw)
        except ValueError:
            error(f"'{raw}' is not a valid integer.")
            continue

        if min_val <= value <= max_val:
            return value
        error(f"Please enter a number between {min_val} and {max_val}.")


def prompt_choice(message: str, choices: Iterable[str]) -> str:
    """
    Prompt until the user picks from a discrete set of options.

    Args:
        message: Prompt text (choices are appended automatically).
        choices: Valid option strings (case-insensitive comparison).

    Returns:
        Validated choice string (lowercased).
    """
    choice_list = [c.lower() for c in choices]
    display = "/".join(choices)
    while True:
        raw = prompt(f"{message} ({display})").lower()
        if raw in choice_list:
            return raw
        error(f"Please enter one of: {display}")


def prompt_date(message: str = "Date (YYYY-MM-DD, leave blank for today)") -> str:
    """
    Prompt for a date string, defaulting to today if left blank.

    Args:
        message: Prompt text.

    Returns:
        ISO-format date string YYYY-MM-DD.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    while True:
        raw = prompt(message, allow_empty=True, default=today)
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            error("Invalid date format. Use YYYY-MM-DD (e.g. 2024-03-15).")


def prompt_menu(choices: Iterable[str], zero_label: str = "Back") -> int:
    """
    Prompt for a numbered menu selection.

    Args:
        choices: Menu option labels (1-indexed for the user).
        zero_label: Label for option 0 (usually 'Back' or 'Exit').

    Returns:
        Integer selection (0 = zero_label, 1..N = item index).
    """
    items = list(choices)
    max_opt = len(items)
    while True:
        try:
            raw = input(f"\n  Enter choice [0-{max_opt}]: ").strip()
            value = int(raw)
            if 0 <= value <= max_opt:
                return value
            error(f"Please enter a number between 0 and {max_opt}.")
        except ValueError:
            error("Please enter a valid number.")
        except KeyboardInterrupt:
            print()
            return 0


def prompt_confirm(message: str = "Are you sure?") -> bool:
    """
    Prompt for a yes/no confirmation.

    Args:
        message: Question text.

    Returns:
        True if the user confirms, False otherwise.
    """
    answer = prompt_choice(message, ["y", "n"])
    return answer == "y"


def prompt_indexed_choice(items: list, label_fn: Callable[[Any], str]) -> Optional[Any]:
    """
    Display a numbered list and return the selected item.

    Args:
        items: List of objects to choose from.
        label_fn: Callable that turns an item into a display string.

    Returns:
        The selected item, or None if the user cancels (0).
    """
    from src.utils.display import colorize, Color

    for i, item in enumerate(items, start=1):
        print(f"    {colorize(str(i), Color.CYAN, Color.BOLD)}. {label_fn(item)}")

    idx = prompt_menu(items, zero_label="Cancel")
    if idx == 0:
        return None
    return items[idx - 1]
