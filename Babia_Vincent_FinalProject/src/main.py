"""
main.py
-------
Entry point and CLI controller for the Personal Finance Tracker.

This module wires together all services and presents an interactive
menu-driven interface to the user.

Run with:
    python -m src.main
  or:
    python src/main.py

Intermediate concepts demonstrated:
  - OOP — App class encapsulating all state and behaviour
  - Exception handling — graceful recovery from all user errors
  - Decorators — used via functools in validators
  - Generators — used inside TransactionService aggregations
  - List comprehensions — used throughout filters and table building
  - Context managers — used in storage and file exports
  - File serialization — JSON persistence + CSV export
"""

import sys
import os
from datetime import datetime
from typing import List

# ---------------------------------------------------------------------------
# Make sure the project root is on the path when running as a script
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.transaction import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from src.services.budget_service import BudgetService
from src.services.report_service import ReportService
from src.services.transaction_service import TransactionService
from src.utils.display import (
    Color, colorize, divider, error, info, print_banner, print_budget_status,
    print_menu, print_summary_card, print_table, section_header, subsection,
    success, warning,
)
from src.utils.storage import JSONStorage
from src.utils.validators import (
    prompt, prompt_choice, prompt_confirm, prompt_date, prompt_float,
    prompt_indexed_choice, prompt_int, prompt_menu,
)


# ---------------------------------------------------------------------------
# App class
# ---------------------------------------------------------------------------

class FinanceTrackerApp:
    """
    Top-level application controller.

    Owns the service layer and delegates all user interactions to dedicated
    menu handler methods.

    Attributes:
        storage (JSONStorage): Shared data store for all services.
        tx_service (TransactionService): Manages transactions.
        budget_service (BudgetService): Manages budgets.
        report_service (ReportService): Handles exports.
    """

    def __init__(self):
        """Initialise all services with a shared storage instance."""
        self.storage = JSONStorage()
        self.tx_service = TransactionService(self.storage)
        self.budget_service = BudgetService(self.storage)
        self.report_service = ReportService()

    # -----------------------------------------------------------------------
    # Main menu
    # -----------------------------------------------------------------------

    def run(self) -> None:
        """Start the application main loop."""
        print_banner()
        self._show_quick_stats()

        main_options = [
            "📥  Add Transaction",
            "📋  View Transactions",
            "🔍  Search & Filter",
            "📊  Reports & Analytics",
            "🎯  Budget Manager",
            "📤  Export Data",
            "🗑️   Delete Transaction",
            "❓  Help & About",
        ]

        while True:
            print_menu("MAIN MENU", main_options)
            choice = prompt_menu(main_options, zero_label="Exit")

            if choice == 0:
                self._exit()
            elif choice == 1:
                self._add_transaction()
            elif choice == 2:
                self._view_transactions_menu()
            elif choice == 3:
                self._search_filter_menu()
            elif choice == 4:
                self._analytics_menu()
            elif choice == 5:
                self._budget_menu()
            elif choice == 6:
                self._export_menu()
            elif choice == 7:
                self._delete_transaction()
            elif choice == 8:
                self._help()

    # -----------------------------------------------------------------------
    # Quick stats bar shown at startup
    # -----------------------------------------------------------------------

    def _show_quick_stats(self) -> None:
        """Display a brief balance summary on startup."""
        income   = self.tx_service.total_income()
        expenses = self.tx_service.total_expenses()
        balance  = self.tx_service.balance()
        n_income, n_expense = self.tx_service.count()

        print_summary_card(income, expenses, balance)
        print(
            colorize(
                f"  Records: {n_income} income | {n_expense} expense | "
                f"{n_income + n_expense} total\n",
                Color.DIM,
            )
        )

        # Over-budget alerts
        spending = self.tx_service.spending_by_category()
        alerts   = self.budget_service.over_budget_alerts(spending)
        if alerts:
            for cat, limit, over in alerts:
                warning(f"OVER BUDGET: {cat} is ₱{over:,.2f} over your ₱{limit:,.2f} limit!")

    # -----------------------------------------------------------------------
    # 1 — Add Transaction
    # -----------------------------------------------------------------------

    def _add_transaction(self) -> None:
        """Interactive flow to record a new income or expense."""
        section_header("ADD TRANSACTION")

        t_type = prompt_choice("Transaction type", ["income", "expense"])

        # Build a numbered category prompt
        valid_cats = sorted(INCOME_CATEGORIES if t_type == "income" else EXPENSE_CATEGORIES)
        subsection("Select Category")
        cat_options = valid_cats
        print_menu("", cat_options)
        cat_idx = prompt_menu(cat_options, zero_label="Cancel")
        if cat_idx == 0:
            return
        category = cat_options[cat_idx - 1]

        amount      = prompt_float("Amount (₱)")
        description = prompt("Description")
        date        = prompt_date()
        tags_raw    = prompt("Tags (comma-separated, or press Enter to skip)", allow_empty=True)
        tags        = [tag.strip() for tag in tags_raw.split(",") if tag.strip()] if tags_raw else []

        try:
            tx = self.tx_service.add_transaction(
                amount=amount,
                category=category,
                description=description,
                date=date,
                transaction_type=t_type,
                tags=tags,
            )
            success(f"Transaction {tx.transaction_id} added — ₱{tx.amount:,.2f} [{tx.category}]")
        except ValueError as exc:
            error(str(exc))

    # -----------------------------------------------------------------------
    # 2 — View Transactions
    # -----------------------------------------------------------------------

    def _view_transactions_menu(self) -> None:
        """Sub-menu for transaction listing options."""
        options = [
            "All Transactions",
            "Income Only",
            "Expenses Only",
            "This Month",
            "By Category",
        ]
        while True:
            print_menu("VIEW TRANSACTIONS", options)
            choice = prompt_menu(options)
            if choice == 0:
                break
            elif choice == 1:
                self._display_transactions(self.tx_service.get_all(), "All Transactions")
            elif choice == 2:
                self._display_transactions(self.tx_service.filter_by_type("income"), "Income")
            elif choice == 3:
                self._display_transactions(self.tx_service.filter_by_type("expense"), "Expenses")
            elif choice == 4:
                now = datetime.now()
                txs = self.tx_service.filter_by_month(now.year, now.month)
                self._display_transactions(txs, f"Transactions — {now.strftime('%B %Y')}")
            elif choice == 5:
                self._view_by_category()

    def _view_by_category(self) -> None:
        """Prompt the user to pick a category and show matching transactions."""
        all_cats = sorted(EXPENSE_CATEGORIES | INCOME_CATEGORIES)
        subsection("Select Category")
        cat = prompt_indexed_choice(all_cats, label_fn=lambda c: c)
        if cat is None:
            return
        txs = self.tx_service.filter_by_category(cat)
        self._display_transactions(txs, f"Category: {cat}")

    def _display_transactions(self, transactions, title: str) -> None:
        """Render a transaction list as a formatted table."""
        section_header(title)
        headers   = ["ID", "Date", "Type", "Category", "Amount (₱)", "Description"]
        col_widths = [10, 12, 9, 14, 12, 24]

        rows = []
        for t in transactions:
            amount_str = colorize(f"{t.amount:>10,.2f}", Color.GREEN if t.transaction_type == "income" else Color.RED)
            rows.append((
                t.transaction_id,
                t.date,
                t.transaction_type.capitalize(),
                t.category,
                amount_str,
                t.description[:24],
            ))

        print_table(headers, rows, col_widths)

    # -----------------------------------------------------------------------
    # 3 — Search & Filter
    # -----------------------------------------------------------------------

    def _search_filter_menu(self) -> None:
        """Sub-menu for search and date-range filtering."""
        options = [
            "Search by Keyword",
            "Filter by Date Range",
            "Filter by Month",
        ]
        while True:
            print_menu("SEARCH & FILTER", options)
            choice = prompt_menu(options)
            if choice == 0:
                break
            elif choice == 1:
                query = prompt("Enter search keyword")
                results = self.tx_service.search(query)
                self._display_transactions(results, f"Search: '{query}'")
            elif choice == 2:
                self._filter_date_range()
            elif choice == 3:
                self._filter_by_month()

    def _filter_date_range(self) -> None:
        """Prompt for start/end dates and show results."""
        section_header("FILTER BY DATE RANGE")
        start = prompt_date("Start date (YYYY-MM-DD)")
        end   = prompt_date("End date (YYYY-MM-DD)")
        if start > end:
            error("Start date cannot be after end date.")
            return
        txs = self.tx_service.filter_by_date_range(start, end)
        self._display_transactions(txs, f"{start} → {end}")

    def _filter_by_month(self) -> None:
        """Prompt for year/month and show results."""
        section_header("FILTER BY MONTH")
        year  = prompt_int("Year (e.g. 2024)", min_val=2000, max_val=2100)
        month = prompt_int("Month (1-12)", min_val=1, max_val=12)
        txs   = self.tx_service.filter_by_month(year, month)
        month_name = datetime(year, month, 1).strftime("%B %Y")
        self._display_transactions(txs, f"Month: {month_name}")

    # -----------------------------------------------------------------------
    # 4 — Analytics
    # -----------------------------------------------------------------------

    def _analytics_menu(self) -> None:
        """Sub-menu for financial reports and analytics."""
        options = [
            "Financial Summary",
            "Spending by Category",
            "Monthly Summary",
            "Top 5 Expenses",
        ]
        while True:
            print_menu("REPORTS & ANALYTICS", options)
            choice = prompt_menu(options)
            if choice == 0:
                break
            elif choice == 1:
                self._show_summary()
            elif choice == 2:
                self._show_spending_by_category()
            elif choice == 3:
                self._show_monthly_summary()
            elif choice == 4:
                self._show_top_expenses()

    def _show_summary(self) -> None:
        """Print the full financial summary card."""
        section_header("FINANCIAL SUMMARY")
        income   = self.tx_service.total_income()
        expenses = self.tx_service.total_expenses()
        balance  = self.tx_service.balance()
        print_summary_card(income, expenses, balance)
        n_income, n_expense = self.tx_service.count()
        info(f"Total records: {n_income + n_expense} ({n_income} income, {n_expense} expense)")

    def _show_spending_by_category(self) -> None:
        """Print a table of expenses grouped by category."""
        section_header("SPENDING BY CATEGORY")
        spending = self.tx_service.spending_by_category()
        if not spending:
            info("No expense records found.")
            return

        total = sum(spending.values())
        rows  = [
            (cat, f"₱{amt:>10,.2f}", f"{(amt / total * 100):5.1f}%")
            for cat, amt in spending.items()
        ]
        print_table(["Category", "Amount (₱)", "% of Total"], rows, [20, 14, 10])
        divider()
        print(colorize(f"  Total Expenses: ₱{total:,.2f}", Color.BOLD))

    def _show_monthly_summary(self) -> None:
        """Print income vs expense totals per calendar month."""
        section_header("MONTHLY SUMMARY")
        monthly = self.tx_service.monthly_summary()
        if not monthly:
            info("No records found.")
            return

        rows = []
        for month, data in monthly.items():
            inc = data.get("income", 0.0)
            exp = data.get("expense", 0.0)
            net = round(inc - exp, 2)
            net_str = colorize(
                f"{'+'if net >= 0 else ''}₱{net:>10,.2f}",
                Color.GREEN if net >= 0 else Color.RED,
            )
            rows.append((month, f"₱{inc:>10,.2f}", f"₱{exp:>10,.2f}", net_str))

        print_table(
            ["Month", "Income", "Expenses", "Net"],
            rows,
            [12, 14, 14, 16],
        )

    def _show_top_expenses(self) -> None:
        """Print the five largest single expense transactions."""
        section_header("TOP 5 EXPENSES")
        top = self.tx_service.top_expenses(5)
        if not top:
            info("No expense records found.")
            return

        rows = [
            (t.transaction_id, t.date, t.category,
             colorize(f"₱{t.amount:>10,.2f}", Color.RED), t.description[:24])
            for t in top
        ]
        print_table(
            ["ID", "Date", "Category", "Amount (₱)", "Description"],
            rows,
            [10, 12, 14, 14, 24],
        )

    # -----------------------------------------------------------------------
    # 5 — Budget Manager
    # -----------------------------------------------------------------------

    def _budget_menu(self) -> None:
        """Sub-menu for setting and reviewing budgets."""
        options = [
            "Set / Update Budget",
            "View Budget Status",
            "Remove a Budget",
        ]
        while True:
            print_menu("BUDGET MANAGER", options)
            choice = prompt_menu(options)
            if choice == 0:
                break
            elif choice == 1:
                self._set_budget()
            elif choice == 2:
                self._view_budget_status()
            elif choice == 3:
                self._remove_budget()

    def _set_budget(self) -> None:
        """Interactive flow to create or update a category budget."""
        section_header("SET BUDGET")
        cats = sorted(EXPENSE_CATEGORIES)
        subsection("Select Category")
        cat = prompt_indexed_choice(cats, label_fn=lambda c: c)
        if cat is None:
            return

        existing = self.budget_service.get_budget(cat)
        if existing:
            info(f"Current budget for {cat}: ₱{existing:,.2f}")

        limit = prompt_float(f"Monthly limit for {cat} (₱)")
        try:
            self.budget_service.set_budget(cat, limit)
            success(f"Budget set: {cat} → ₱{limit:,.2f} / month")
        except ValueError as exc:
            error(str(exc))

    def _view_budget_status(self) -> None:
        """Print a progress-bar summary of each category budget vs actual spend."""
        section_header("BUDGET STATUS")
        budgets  = self.budget_service.get_all_budgets()
        if not budgets:
            info("No budgets configured yet. Use 'Set / Update Budget' to add one.")
            return

        spending = self.tx_service.spending_by_category()
        results  = self.budget_service.evaluate(spending)

        print()
        for cat, limit, spent, remaining in results:
            print_budget_status(cat, limit, spent)
        print()

        alerts = self.budget_service.over_budget_alerts(spending)
        if alerts:
            for cat, limit, over in alerts:
                warning(f"{cat}: ₱{over:,.2f} over budget!")
        else:
            success("All categories within budget. Great job! 🎉")

    def _remove_budget(self) -> None:
        """Interactive flow to delete a budget entry."""
        section_header("REMOVE BUDGET")
        budgets = self.budget_service.get_all_budgets()
        if not budgets:
            info("No budgets to remove.")
            return

        cats = list(budgets.keys())
        cat  = prompt_indexed_choice(cats, label_fn=lambda c: f"{c} (₱{budgets[c]:,.2f})")
        if cat is None:
            return

        if prompt_confirm(f"Remove budget for {cat}?"):
            self.budget_service.remove_budget(cat)
            success(f"Budget for {cat} removed.")

    # -----------------------------------------------------------------------
    # 6 — Export
    # -----------------------------------------------------------------------

    def _export_menu(self) -> None:
        """Sub-menu for data export options."""
        options = [
            "Export All Transactions (CSV)",
            "Export Current Month (CSV)",
            "Export Summary Report (TXT)",
            "Create Data Backup (JSON)",
        ]
        while True:
            print_menu("EXPORT DATA", options)
            choice = prompt_menu(options)
            if choice == 0:
                break
            elif choice == 1:
                path = self.report_service.export_csv(self.tx_service.get_all())
                success(f"Exported to: {path}")
            elif choice == 2:
                now  = datetime.now()
                path = self.report_service.monthly_csv(
                    self.tx_service.get_all(), now.year, now.month
                )
                success(f"Exported to: {path}")
            elif choice == 3:
                path = self.report_service.summary_txt(
                    income=self.tx_service.total_income(),
                    expenses=self.tx_service.total_expenses(),
                    balance=self.tx_service.balance(),
                    spending_by_category=self.tx_service.spending_by_category(),
                )
                success(f"Summary written to: {path}")
            elif choice == 4:
                path = self.storage.backup()
                success(f"Backup created: {path}")

    # -----------------------------------------------------------------------
    # 7 — Delete Transaction
    # -----------------------------------------------------------------------

    def _delete_transaction(self) -> None:
        """Interactive flow to delete a transaction by ID."""
        section_header("DELETE TRANSACTION")
        txs = self.tx_service.get_all()
        if not txs:
            info("No transactions to delete.")
            return

        # Let the user pick from the list
        subsection("Select Transaction to Delete")
        tx = prompt_indexed_choice(
            txs,
            label_fn=lambda t: (
                f"{t.transaction_id}  {t.date}  "
                f"{'+'if t.transaction_type=='income' else '-'}₱{t.amount:,.2f}  "
                f"{t.category}  {t.description[:30]}"
            ),
        )
        if tx is None:
            return

        if prompt_confirm(
            f"Delete {tx.transaction_id} (₱{tx.amount:,.2f} — {tx.description[:30]})?"
        ):
            self.tx_service.delete_transaction(tx.transaction_id)
            success(f"Transaction {tx.transaction_id} deleted.")
        else:
            info("Deletion cancelled.")

    # -----------------------------------------------------------------------
    # 8 — Help
    # -----------------------------------------------------------------------

    def _help(self) -> None:
        """Display help and about information."""
        section_header("HELP & ABOUT")
        help_text = f"""
  {colorize('Personal Finance Tracker v1.0', Color.CYAN, Color.BOLD)}
  {colorize('Developed as an Intermediate Python Final Project', Color.DIM)}

  {colorize('FEATURES', Color.YELLOW, Color.BOLD)}
  ─────────────────────────────────────────────
  • Add income and expense transactions
  • Categorise and tag transactions
  • View, search, and filter records
  • Set monthly budgets per category
  • Visual budget progress bars with alerts
  • Analytics: spending breakdown, monthly trends
  • Top-5 expense report
  • Export data to CSV and TXT reports
  • Automatic JSON backup

  {colorize('INTERMEDIATE PYTHON CONCEPTS USED', Color.YELLOW, Color.BOLD)}
  ─────────────────────────────────────────────
  • Object-Oriented Programming (classes, encapsulation)
  • List comprehensions and generator expressions
  • Decorators (functools.wraps)
  • Context managers (with open / json)
  • Exception handling (try / except / raise from)
  • File serialisation (JSON persistence, CSV export)
  • Sorting & searching algorithms
  • Data structures (lists, dicts, sets, tuples, frozensets)

  {colorize('DATA STORAGE', Color.YELLOW, Color.BOLD)}
  ─────────────────────────────────────────────
  • All data is saved in:  data/finance_data.json
  • Backups are written to: data/finance_data_backup_*.json
  • CSV exports land in:   data/*.csv

  {colorize('KEYBOARD SHORTCUT', Color.YELLOW, Color.BOLD)}
  ─────────────────────────────────────────────
  • Press Ctrl+C at any prompt to return to the menu safely.
"""
        print(help_text)

    # -----------------------------------------------------------------------
    # Exit
    # -----------------------------------------------------------------------

    def _exit(self) -> None:
        """Confirm exit and shut down gracefully."""
        if prompt_confirm("Exit the application?"):
            print(colorize("\n  Thank you for using Personal Finance Tracker. Goodbye! 👋\n", Color.CYAN))
            sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Application entry point — construct and run the app."""
    try:
        app = FinanceTrackerApp()
        app.run()
    except KeyboardInterrupt:
        print(colorize("\n\n  Interrupted. Goodbye!\n", Color.YELLOW))
        sys.exit(0)


if __name__ == "__main__":
    main()
