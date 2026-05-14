"""
display.py
----------
Terminal formatting helpers for the Finance Tracker CLI.

Provides coloured output, table rendering, and banner printing so that all
presentation logic stays outside business-logic modules.

Intermediate concepts demonstrated:
  - ANSI escape codes for terminal colours
  - String formatting with f-strings and format specs
  - Generator functions (table row generation)
  - Decorator pattern (section header wrapper)
"""

from functools import wraps
from typing import Iterable, List


# ---------------------------------------------------------------------------
# ANSI colour codes
# ---------------------------------------------------------------------------

class Color:
    """ANSI escape code constants for terminal colouring."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Foreground colours
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

    # Background colours
    BG_BLUE  = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_RED   = "\033[41m"


def colorize(text: str, *codes: str) -> str:
    """Wrap *text* in ANSI colour codes."""
    return "".join(codes) + str(text) + Color.RESET


# ---------------------------------------------------------------------------
# Banners & section headers
# ---------------------------------------------------------------------------

APP_BANNER = f"""
{Color.CYAN}{Color.BOLD}
╔══════════════════════════════════════════════════════════╗
║           💰  PERSONAL FINANCE TRACKER  💰              ║
║              Smart Money. Smarter Decisions.             ║
╚══════════════════════════════════════════════════════════╝
{Color.RESET}"""

def print_banner() -> None:
    """Print the application title banner."""
    print(APP_BANNER)


def section_header(title: str) -> None:
    """Print a visually distinct section header."""
    width = 60
    bar = "─" * width
    print(f"\n{Color.CYAN}{Color.BOLD}┌{bar}┐")
    print(f"│  {title:<{width - 2}}│")
    print(f"└{bar}┘{Color.RESET}")


def subsection(title: str) -> None:
    """Print a lighter subsection label."""
    print(f"\n{Color.YELLOW}{Color.BOLD}  ▸ {title}{Color.RESET}")


# ---------------------------------------------------------------------------
# Menu helpers
# ---------------------------------------------------------------------------

def print_menu(title: str, options: List[str]) -> None:
    """
    Print a numbered CLI menu.

    Args:
        title: Menu section heading.
        options: List of option labels (automatically numbered from 1).
    """
    section_header(title)
    for i, option in enumerate(options, start=1):
        num = colorize(f" {i:>2}.", Color.CYAN, Color.BOLD)
        print(f"  {num}  {option}")
    print()


def divider(char: str = "─", width: int = 62) -> None:
    """Print a horizontal divider line."""
    print(colorize(char * width, Color.GRAY))


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------

def _row_generator(rows: Iterable[tuple], col_widths: List[int]):
    """
    Generator that yields formatted table row strings.

    Args:
        rows: Iterable of tuples, one per row.
        col_widths: List of column widths (same length as each row tuple).
    """
    for row in rows:
        cells = (str(cell)[:w].ljust(w) for cell, w in zip(row, col_widths))
        yield "  " + "  ".join(cells)


def print_table(
    headers: List[str],
    rows: List[tuple],
    col_widths: List[int],
    title: str = "",
) -> None:
    """
    Render a formatted table in the terminal.

    Args:
        headers: Column header labels.
        rows: List of data tuples.
        col_widths: Character width for each column.
        title: Optional heading printed above the table.
    """
    if title:
        subsection(title)

    # Header row
    header_cells = [
        colorize(h[:w].ljust(w), Color.BOLD, Color.WHITE)
        for h, w in zip(headers, col_widths)
    ]
    print("  " + "  ".join(header_cells))
    divider("─", sum(col_widths) + 2 * len(col_widths))

    if not rows:
        print(colorize("  (No records found)", Color.GRAY))
        return

    # Data rows — use the generator
    for line in _row_generator(rows, col_widths):
        print(line)

    divider("─", sum(col_widths) + 2 * len(col_widths))
    print(colorize(f"  {len(rows)} record(s) displayed.", Color.DIM))


# ---------------------------------------------------------------------------
# Status / feedback messages
# ---------------------------------------------------------------------------

def success(msg: str) -> None:
    """Print a green success message."""
    print(f"\n  {colorize('✔', Color.GREEN, Color.BOLD)}  {msg}")


def error(msg: str) -> None:
    """Print a red error message."""
    print(f"\n  {colorize('✘', Color.RED, Color.BOLD)}  {colorize(msg, Color.RED)}")


def warning(msg: str) -> None:
    """Print a yellow warning message."""
    print(f"\n  {colorize('⚠', Color.YELLOW, Color.BOLD)}  {msg}")


def info(msg: str) -> None:
    """Print a cyan informational message."""
    print(f"\n  {colorize('ℹ', Color.CYAN, Color.BOLD)}  {msg}")


# ---------------------------------------------------------------------------
# Summary card
# ---------------------------------------------------------------------------

def print_summary_card(income: float, expenses: float, balance: float) -> None:
    """
    Print a three-column financial summary card.

    Args:
        income: Total income amount.
        expenses: Total expenses amount.
        balance: Net balance (income − expenses).
    """
    balance_color = Color.GREEN if balance >= 0 else Color.RED
    balance_sign  = "+" if balance >= 0 else ""

    print(f"""
{Color.BOLD}  ┌────────────────────┬─────────────────────┬─────────────────────┐
  │  💚 Total Income   │  💔 Total Expenses  │  💼 Net Balance     │
  ├────────────────────┼─────────────────────┼─────────────────────┤
  │  {Color.GREEN}₱{income:>16,.2f}{Color.RESET}{Color.BOLD}  │  {Color.RED}₱{expenses:>17,.2f}{Color.RESET}{Color.BOLD}  │  {balance_color}{balance_sign}₱{abs(balance):>16,.2f}{Color.RESET}{Color.BOLD}  │
  └────────────────────┴─────────────────────┴─────────────────────┘{Color.RESET}""")


def print_budget_status(category: str, budget: float, spent: float) -> None:
    """
    Render a single-category budget status bar.

    Args:
        category: Budget category name.
        budget: Budget limit.
        spent: Amount spent so far.
    """
    pct = min((spent / budget * 100) if budget > 0 else 0, 100)
    bar_fill = int(pct / 5)  # 20-char bar
    bar = "█" * bar_fill + "░" * (20 - bar_fill)
    color = Color.GREEN if pct < 70 else (Color.YELLOW if pct < 90 else Color.RED)
    remaining = budget - spent

    remaining_str = (
        colorize(f"₱{remaining:,.2f} left", Color.GREEN)
        if remaining >= 0
        else colorize(f"₱{abs(remaining):,.2f} over!", Color.RED, Color.BOLD)
    )

    print(
        f"  {category:<15} {color}{bar}{Color.RESET} "
        f"{pct:5.1f}%  {remaining_str}"
    )
