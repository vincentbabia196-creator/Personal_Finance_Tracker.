"""
budget_service.py
-----------------
Business-logic layer for managing monthly spending budgets per category.

Intermediate concepts demonstrated:
  - Dictionary-based data storage
  - Comparison algorithms (budget vs actual spend)
  - Separation of concerns (budget logic isolated from transaction logic)
"""

from typing import Dict, List, Optional, Tuple

from src.utils.storage import JSONStorage


class BudgetService:
    """
    Manages category-level monthly spending budgets.

    Budgets are stored as a flat dict:  {category: limit_float}.

    Attributes:
        _storage (JSONStorage): Underlying data store.
        _budgets (dict[str, float]): In-memory budget limits.
    """

    def __init__(self, storage: JSONStorage):
        """
        Initialise the service and load existing budgets.

        Args:
            storage: A configured JSONStorage instance.
        """
        self._storage = storage
        self._budgets: Dict[str, float] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load budgets from storage into memory."""
        self._budgets = self._storage.get("budgets", {})

    def _save(self) -> None:
        """Persist in-memory budgets to storage."""
        self._storage.set("budgets", self._budgets)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def set_budget(self, category: str, limit: float) -> None:
        """
        Create or update the spending limit for a category.

        Args:
            category: Category name.
            limit: Maximum spend (positive float).

        Raises:
            ValueError: If limit is not positive.
        """
        if limit <= 0:
            raise ValueError("Budget limit must be a positive number.")
        self._budgets[category] = round(limit, 2)
        self._save()

    def remove_budget(self, category: str) -> bool:
        """
        Delete a budget entry.

        Args:
            category: Category to remove.

        Returns:
            True if removed, False if it did not exist.
        """
        if category in self._budgets:
            del self._budgets[category]
            self._save()
            return True
        return False

    def get_budget(self, category: str) -> Optional[float]:
        """Return the budget limit for *category*, or None if not set."""
        return self._budgets.get(category)

    def get_all_budgets(self) -> Dict[str, float]:
        """Return a copy of all budget limits, sorted alphabetically."""
        return dict(sorted(self._budgets.items()))

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def evaluate(
        self,
        spending_by_category: Dict[str, float],
    ) -> List[Tuple[str, float, float, float]]:
        """
        Compare budgets against actual spending.

        Args:
            spending_by_category: Dict of {category: amount_spent} from
                TransactionService.spending_by_category().

        Returns:
            List of tuples: (category, budget, spent, remaining).
            Categories with no budget that have spending are excluded.
        """
        results = []
        for category, limit in self._budgets.items():
            spent = spending_by_category.get(category, 0.0)
            remaining = round(limit - spent, 2)
            results.append((category, limit, spent, remaining))
        # Sort: over-budget first, then by % used descending
        return sorted(
            results,
            key=lambda r: (r[1] - r[2]) / r[1] if r[1] > 0 else 0,
        )

    def over_budget_alerts(
        self,
        spending_by_category: Dict[str, float],
    ) -> List[Tuple[str, float, float]]:
        """
        Return categories where spending has exceeded the budget.

        Args:
            spending_by_category: Dict from TransactionService.

        Returns:
            List of (category, budget_limit, amount_over).
        """
        return [
            (cat, limit, round(spending_by_category.get(cat, 0) - limit, 2))
            for cat, limit in self._budgets.items()
            if spending_by_category.get(cat, 0) > limit
        ]
