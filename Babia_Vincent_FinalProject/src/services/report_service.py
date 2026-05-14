"""
report_service.py
-----------------
Generates exportable reports from transaction data.

Intermediate concepts demonstrated:
  - CSV file writing with the csv standard library
  - Context managers (with open(...))
  - List comprehensions for data transformation
  - pathlib for cross-platform path handling
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.transaction import Transaction

DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[2] / "data"


class ReportService:
    """
    Handles data export and report generation.

    Attributes:
        export_dir (Path): Directory where exported files are written.
    """

    def __init__(self, export_dir: Path = DEFAULT_EXPORT_DIR):
        """
        Initialise the report service.

        Args:
            export_dir: Directory to write output files into.
        """
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, transactions: List["Transaction"], filename: str = "") -> Path:
        """
        Export a list of transactions to a CSV file.

        The file is saved in ``export_dir`` with a timestamped filename if
        none is provided.

        Args:
            transactions: Records to export.
            filename: Optional filename (without path).

        Returns:
            Path to the written CSV file.

        Raises:
            OSError: If the file cannot be written.
        """
        if not filename:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transactions_{stamp}.csv"

        out_path = self.export_dir / filename

        fieldnames = [
            "transaction_id", "date", "type", "category",
            "amount", "description", "tags",
        ]

        with open(out_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(
                {
                    "transaction_id": t.transaction_id,
                    "date": t.date,
                    "type": t.transaction_type,
                    "category": t.category,
                    "amount": f"{t.amount:.2f}",
                    "description": t.description,
                    "tags": "|".join(t.tags),
                }
                for t in transactions
            )

        return out_path

    def monthly_csv(
        self,
        transactions: List["Transaction"],
        year: int,
        month: int,
    ) -> Path:
        """
        Export transactions for a single month to CSV.

        Args:
            transactions: Full unfiltered transaction list.
            year: Target year.
            month: Target month (1-12).

        Returns:
            Path to the generated CSV file.
        """
        prefix = f"{year:04d}-{month:02d}"
        filtered = [t for t in transactions if t.date.startswith(prefix)]
        filename = f"report_{prefix}.csv"
        return self.export_csv(filtered, filename)

    def summary_txt(
        self,
        income: float,
        expenses: float,
        balance: float,
        spending_by_category: dict,
    ) -> Path:
        """
        Write a plain-text financial summary report.

        Args:
            income: Total income.
            expenses: Total expenses.
            balance: Net balance.
            spending_by_category: Category breakdown dict.

        Returns:
            Path to the written .txt file.
        """
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = self.export_dir / f"summary_{stamp}.txt"
        now_str  = datetime.now().strftime("%B %d, %Y %H:%M")

        lines = [
            "=" * 55,
            "       PERSONAL FINANCE TRACKER — SUMMARY REPORT",
            f"       Generated: {now_str}",
            "=" * 55,
            "",
            f"  Total Income  : ₱{income:>14,.2f}",
            f"  Total Expenses: ₱{expenses:>14,.2f}",
            f"  Net Balance   : ₱{balance:>14,.2f}",
            "",
            "-" * 55,
            "  SPENDING BY CATEGORY",
            "-" * 55,
        ]

        for cat, amt in spending_by_category.items():
            lines.append(f"  {cat:<20}: ₱{amt:>10,.2f}")

        lines += ["", "=" * 55, "  End of Report", "=" * 55]

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        return out_path
