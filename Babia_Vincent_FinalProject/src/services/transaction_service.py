"""
transaction_service.py
----------------------
Business-logic layer for managing financial transactions.

All CRUD operations, sorting, filtering, and statistical calculations live here.
The service never touches the CLI; it only operates on domain objects and the
storage layer.

Intermediate concepts demonstrated:
  - List comprehensions
  - Sorting with lambda key functions and operator.attrgetter
  - Generator-based aggregation
  - Exception chaining (raise ... from ...)
  - UUID-based ID generation
"""

import uuid
from datetime import datetime
from typing import Dict, Generator, List, Optional, Tuple

from src.models.transaction import Transaction
from src.utils.storage import JSONStorage, StorageError


class TransactionService:
    """
    Manages the full lifecycle of Transaction records.

    Responsibilities:
      - Add, delete, and list transactions.
      - Persist and load records via a JSONStorage instance.
      - Provide summary statistics and filtered views.

    Attributes:
        _storage (JSONStorage): Underlying data store.
        _transactions (list[Transaction]): In-memory list of all transactions.
    """

    def __init__(self, storage: JSONStorage):
        """
        Initialise the service and load existing records.

        Args:
            storage: A configured JSONStorage instance.
        """
        self._storage = storage
        self._transactions: List[Transaction] = []
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load transaction records from the storage layer into memory."""
        raw_list = self._storage.get("transactions", [])
        self._transactions = [Transaction.from_dict(d) for d in raw_list]

    def _save(self) -> None:
        """Persist the in-memory transaction list to the storage layer."""
        data = self._storage.load()
        data["transactions"] = [t.to_dict() for t in self._transactions]
        self._storage.save(data)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def add_transaction(
        self,
        amount: float,
        category: str,
        description: str,
        date: str,
        transaction_type: str,
        tags: Optional[List[str]] = None,
    ) -> Transaction:
        """
        Create and persist a new transaction.

        Args:
            amount: Positive float amount.
            category: Valid category string.
            description: Short description.
            date: ISO date string (YYYY-MM-DD).
            transaction_type: 'income' or 'expense'.
            tags: Optional keyword tags.

        Returns:
            The newly created Transaction.

        Raises:
            ValueError: If any argument fails model-level validation.
        """
        t_id = str(uuid.uuid4())[:8].upper()
        transaction = Transaction(
            transaction_id=t_id,
            amount=amount,
            category=category,
            description=description,
            date=date,
            transaction_type=transaction_type,
            tags=tags or [],
        )
        self._transactions.append(transaction)
        self._save()
        return transaction

    def delete_transaction(self, transaction_id: str) -> bool:
        """
        Remove a transaction by its ID.

        Args:
            transaction_id: The ID to look up (case-insensitive).

        Returns:
            True if found and deleted, False if not found.
        """
        upper_id = transaction_id.upper()
        before = len(self._transactions)
        self._transactions = [
            t for t in self._transactions if t.transaction_id != upper_id
        ]
        if len(self._transactions) < before:
            self._save()
            return True
        return False

    def get_all(self, sort_by: str = "date", reverse: bool = True) -> List[Transaction]:
        """
        Return all transactions sorted by a given attribute.

        Args:
            sort_by: Attribute name to sort by ('date', 'amount', 'category').
            reverse: Descending order when True (default).

        Returns:
            Sorted list of Transaction objects.
        """
        valid_keys = {"date", "amount", "category", "transaction_type"}
        key = sort_by if sort_by in valid_keys else "date"
        return sorted(self._transactions, key=lambda t: getattr(t, key), reverse=reverse)

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """
        Find a single transaction by its ID.

        Args:
            transaction_id: ID to search for (case-insensitive).

        Returns:
            Matching Transaction or None.
        """
        upper_id = transaction_id.upper()
        return next((t for t in self._transactions if t.transaction_id == upper_id), None)

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def filter_by_type(self, t_type: str) -> List[Transaction]:
        """Return transactions matching a given type ('income'/'expense')."""
        return [t for t in self._transactions if t.transaction_type == t_type.lower()]

    def filter_by_category(self, category: str) -> List[Transaction]:
        """Return transactions in a specific category."""
        return [t for t in self._transactions if t.category.lower() == category.lower()]

    def filter_by_month(self, year: int, month: int) -> List[Transaction]:
        """
        Return transactions that fall within a given calendar month.

        Args:
            year: Four-digit year.
            month: Month number (1-12).

        Returns:
            Filtered list sorted by date descending.
        """
        prefix = f"{year:04d}-{month:02d}"
        filtered = [t for t in self._transactions if t.date.startswith(prefix)]
        return sorted(filtered, key=lambda t: t.date, reverse=True)

    def filter_by_date_range(self, start: str, end: str) -> List[Transaction]:
        """
        Return transactions whose date falls in [start, end] (inclusive).

        Args:
            start: ISO date string for the range start.
            end: ISO date string for the range end.

        Returns:
            Filtered and date-sorted list.
        """
        return sorted(
            [t for t in self._transactions if start <= t.date <= end],
            key=lambda t: t.date,
            reverse=True,
        )

    def search(self, query: str) -> List[Transaction]:
        """
        Full-text search across description, category, and tags.

        Args:
            query: Case-insensitive search term.

        Returns:
            Matching transactions.
        """
        q = query.lower()
        return [
            t for t in self._transactions
            if (q in t.description.lower()
                or q in t.category.lower()
                or any(q in tag.lower() for tag in t.tags))
        ]

    # ------------------------------------------------------------------
    # Statistics & aggregations
    # ------------------------------------------------------------------

    def _income_generator(self) -> Generator[float, None, None]:
        """Generator that yields amounts for all income transactions."""
        return (t.amount for t in self._transactions if t.transaction_type == "income")

    def _expense_generator(self) -> Generator[float, None, None]:
        """Generator that yields amounts for all expense transactions."""
        return (t.amount for t in self._transactions if t.transaction_type == "expense")

    def total_income(self) -> float:
        """Return the sum of all income transaction amounts."""
        return round(sum(self._income_generator()), 2)

    def total_expenses(self) -> float:
        """Return the sum of all expense transaction amounts."""
        return round(sum(self._expense_generator()), 2)

    def balance(self) -> float:
        """Return net balance (income − expenses)."""
        return round(self.total_income() - self.total_expenses(), 2)

    def spending_by_category(self) -> Dict[str, float]:
        """
        Aggregate expense amounts grouped by category.

        Returns:
            Dict mapping category → total amount, sorted descending by value.
        """
        totals: Dict[str, float] = {}
        for t in self._transactions:
            if t.transaction_type == "expense":
                totals[t.category] = round(totals.get(t.category, 0.0) + t.amount, 2)
        return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))

    def monthly_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Aggregate income and expense totals per calendar month.

        Returns:
            Dict mapping 'YYYY-MM' → {'income': float, 'expense': float}.
        """
        summary: Dict[str, Dict[str, float]] = {}
        for t in self._transactions:
            month_key = t.date[:7]  # 'YYYY-MM'
            if month_key not in summary:
                summary[month_key] = {"income": 0.0, "expense": 0.0}
            summary[month_key][t.transaction_type] = round(
                summary[month_key][t.transaction_type] + t.amount, 2
            )
        return dict(sorted(summary.items(), reverse=True))

    def top_expenses(self, n: int = 5) -> List[Transaction]:
        """
        Return the N largest expense transactions.

        Args:
            n: Number of top records to return.

        Returns:
            List sorted by amount descending.
        """
        expenses = [t for t in self._transactions if t.transaction_type == "expense"]
        return sorted(expenses, key=lambda t: t.amount, reverse=True)[:n]

    def count(self) -> Tuple[int, int]:
        """
        Return the count of income and expense transactions.

        Returns:
            Tuple of (income_count, expense_count).
        """
        income_count  = sum(1 for t in self._transactions if t.transaction_type == "income")
        expense_count = sum(1 for t in self._transactions if t.transaction_type == "expense")
        return income_count, expense_count
