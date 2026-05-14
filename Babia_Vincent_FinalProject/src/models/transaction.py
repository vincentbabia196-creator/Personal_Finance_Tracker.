"""
transaction.py
--------------
Defines the Transaction data model used throughout the Finance Tracker application.

This module provides the core data structure for representing income and expense
records, including serialization to/from dictionary format for JSON persistence.
"""

from datetime import datetime
from typing import Optional


# Valid category sets for validation
EXPENSE_CATEGORIES: frozenset = frozenset({
    "Food", "Transport", "Housing", "Utilities", "Healthcare",
    "Entertainment", "Shopping", "Education", "Personal", "Other"
})

INCOME_CATEGORIES: frozenset = frozenset({
    "Salary", "Freelance", "Investment", "Gift", "Business", "Other"
})

VALID_TYPES: tuple = ("income", "expense")


class Transaction:
    """
    Represents a single financial transaction (income or expense).

    Attributes:
        transaction_id (str): Unique identifier for the transaction.
        amount (float): Monetary value of the transaction.
        category (str): Category label (e.g., 'Food', 'Salary').
        description (str): Short human-readable note about the transaction.
        date (str): ISO-format date string (YYYY-MM-DD).
        transaction_type (str): Either 'income' or 'expense'.
        tags (list[str]): Optional user-defined tags for filtering.
    """

    def __init__(
        self,
        transaction_id: str,
        amount: float,
        category: str,
        description: str,
        date: str,
        transaction_type: str,
        tags: Optional[list] = None,
    ):
        """
        Initialise a Transaction instance.

        Args:
            transaction_id: Unique string ID.
            amount: Positive float amount.
            category: Must belong to the valid category set for the type.
            description: Free-text description.
            date: Date string in YYYY-MM-DD format.
            transaction_type: 'income' or 'expense'.
            tags: Optional list of string tags.

        Raises:
            ValueError: If any argument fails validation.
        """
        self._validate(amount, category, date, transaction_type)

        self.transaction_id = transaction_id
        self.amount = round(float(amount), 2)
        self.category = category
        self.description = description.strip()
        self.date = date
        self.transaction_type = transaction_type.lower()
        self.tags = tags if tags else []

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(amount, category, date, transaction_type):
        """Run field-level validation and raise ValueError on failure."""
        if float(amount) <= 0:
            raise ValueError("Amount must be a positive number.")

        t_type = transaction_type.lower()
        if t_type not in VALID_TYPES:
            raise ValueError(f"Type must be one of: {VALID_TYPES}")

        valid_cats = INCOME_CATEGORIES if t_type == "income" else EXPENSE_CATEGORIES
        if category not in valid_cats:
            raise ValueError(
                f"Invalid category '{category}'. Valid options: {sorted(valid_cats)}"
            )

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the transaction to a plain dictionary (JSON-safe)."""
        return {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date,
            "transaction_type": self.transaction_type,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """
        Deserialize a Transaction from a dictionary.

        Args:
            data: Dictionary as produced by ``to_dict()``.

        Returns:
            A fully constructed Transaction instance.
        """
        return cls(
            transaction_id=data["transaction_id"],
            amount=data["amount"],
            category=data["category"],
            description=data["description"],
            date=data["date"],
            transaction_type=data["transaction_type"],
            tags=data.get("tags", []),
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        sign = "+" if self.transaction_type == "income" else "-"
        return (
            f"Transaction({self.transaction_id}, {sign}₱{self.amount:.2f}, "
            f"{self.category}, {self.date})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.transaction_id == other.transaction_id

    def __hash__(self) -> int:
        return hash(self.transaction_id)
