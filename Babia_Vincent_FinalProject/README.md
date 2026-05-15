# 💰 Personal Finance Tracker

> **Smart Money. Smarter Decisions.**
> A professional CLI-based personal finance management system built with Python, demonstrating intermediate programming concepts through real-world application.

---

## 📋 Project Description

Personal Finance Tracker is a fully-featured command-line application that helps users manage their income and expenses, set monthly budgets, view spending analytics, and export financial reports — all from the terminal.

The project was developed as an **Intermediate Python Programming Final Project**, showcasing clean architecture, Object-Oriented Programming (OOP), and several advanced Python concepts in a realistic, user-friendly application.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📥 **Add Transactions** | Record income and expense entries with categories, descriptions, dates, and custom tags |
| 📋 **View Transactions** | Browse all records or filter by type, category, or month in formatted tables |
| 🔍 **Search & Filter** | Full-text keyword search, date-range filtering, and monthly views |
| 📊 **Analytics** | Financial summary, spending-by-category breakdown, monthly trends, top-5 expenses |
| 🎯 **Budget Manager** | Set monthly limits per category with visual progress bars and over-budget alerts |
| 📤 **Export Data** | Export transactions to CSV, generate TXT summary reports, create JSON backups |
| 🗑️ **Delete Records** | Safely remove transactions with confirmation prompts |
| 💾 **Auto-Save** | All data persisted instantly to JSON — no manual saves needed |

---

## 🧠 Intermediate Python Concepts Demonstrated

1. **Object-Oriented Programming** — `Transaction`, `TransactionService`, `BudgetService`, `ReportService`, `JSONStorage`, `FinanceTrackerApp` classes with encapsulation and single responsibility
2. **List Comprehensions** — Used throughout filtering, table-building, and aggregation (`spending_by_category`, `filter_by_type`, `search`)
3. **Generator Expressions** — `_income_generator()` and `_expense_generator()` in `TransactionService`; table row generator in `display.py`
4. **Decorators** — `functools.wraps` used in validator helpers
5. **Context Managers** — `with open(...)` in `JSONStorage._write()`, CSV export, and TXT report generation
6. **Exception Handling** — `try/except/raise from` chains throughout validation, storage, and CLI layers
7. **File Serialization** — JSON persistence with atomic write-then-rename; CSV export via `csv.DictWriter`
8. **Sorting & Searching** — Multi-key sorts with `lambda` and `operator`; full-text search across multiple fields
9. **Data Structures** — `list`, `dict`, `set`, `frozenset`, `tuple` all used semantically throughout the codebase
10. **Type Hints** — `Optional`, `List`, `Dict`, `Tuple`, `Generator` from `typing` throughout all modules

---

## 🗂️ Project Structure

```
finance_tracker/
├── README.md                    ← Project documentation
├── requirements.txt             ← Dependency list (stdlib only)
├── data/
│   └── finance_data.json        ← Sample dataset (24 transactions, 9 budgets)
└── src/
    ├── main.py                  ← CLI entry point & App controller
    ├── models/
    │   ├── __init__.py
    │   └── transaction.py       ← Transaction data model
    ├── services/
    │   ├── __init__.py
    │   ├── transaction_service.py  ← CRUD, filtering, analytics
    │   ├── budget_service.py       ← Budget management & alerts
    │   └── report_service.py       ← CSV / TXT export
    └── utils/
        ├── __init__.py
        ├── display.py           ← ANSI colours, tables, banners
        ├── storage.py           ← JSON persistence layer
        └── validators.py        ← Safe CLI input helpers
```

---

## ⚙️ Installation Guide

### Prerequisites
- Python **3.8 or higher**
- No third-party packages required — uses the Python standard library only

### Steps

```bash
# 1. Clone or download the project
git clone https://github.com/yourusername/finance-tracker.git
cd finance-tracker

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Verify Python version
python --version                # Should be 3.8+

# 4. Run the application
python src/main.py
```

> **Note:** The project ships with a sample dataset (`data/finance_data.json`) containing 24 transactions across 3 months and 9 preset budgets so you can explore all features immediately.

---

## 🚀 Usage Instructions

### Starting the App
```bash
python src/main.py
```

### Main Menu Navigation

```
╔══════════════════════════════════════════════════════════╗
║           💰  PERSONAL FINANCE TRACKER  💰              ║
║              Smart Money. Smarter Decisions.             ║
╚══════════════════════════════════════════════════════════╝

  ┌────────────────────┬─────────────────────┬─────────────────────┐
  │  💚 Total Income   │  💔 Total Expenses  │  💼 Net Balance     │
  ├────────────────────┼─────────────────────┼─────────────────────┤
  │  ₱      159,500.00 │  ₱        56,048.00 │  +₱      103,452.00 │
  └────────────────────┴─────────────────────┴─────────────────────┘

  MAIN MENU
   1. 📥  Add Transaction
   2. 📋  View Transactions
   3. 🔍  Search & Filter
   4. 📊  Reports & Analytics
   5. 🎯  Budget Manager
   6. 📤  Export Data
   7. 🗑️   Delete Transaction
   8. ❓  Help & About
   0. Exit

  Enter choice [0-8]:
```

### Adding a Transaction
```
  Transaction type (income/expense): expense
  Select Category → 3. Food
  Amount (₱): 350
  Description: Jollibee lunch
  Date (YYYY-MM-DD, leave blank for today): [Enter]
  Tags (comma-separated, or press Enter to skip): food, dining
  ✔  Transaction 9F2A1B3C added — ₱350.00 [Food]
```

### Viewing Budget Status
```
  Housing         ████████████████████ 100.0%  ₱16,500.00 over!
  Food            ████████████████████  80.0%  ₱1,200.00 left
  Education       ████████████░░░░░░░░  60.0%  ₱400.00 left
  Healthcare      ████░░░░░░░░░░░░░░░░  20.0%  ₱1,600.00 left
```

### Keyboard Shortcuts
| Key | Action |
|---|---|
| `0` + Enter | Go back / Exit current menu |
| `Ctrl+C` | Cancel current prompt safely |

---

## 📸 Sample Output

### Financial Summary Card
```
  ┌────────────────────┬─────────────────────┬─────────────────────┐
  │  💚 Total Income   │  💔 Total Expenses  │  💼 Net Balance     │
  ├────────────────────┼─────────────────────┼─────────────────────┤
  │  ₱      159,500.00 │  ₱        56,048.00 │  +₱      103,452.00 │
  └────────────────────┴─────────────────────┴─────────────────────┘
```

### Transaction Table
```
  ID          Date          Type       Category        Amount (₱)    Description
  ─────────────────────────────────────────────────────────────────────────────
  S9T0U1V2    2024-05-01    Income     Salary          +45,000.00    Monthly salary - May
  T0U1V2W3    2024-05-03    Expense    Housing          -8,500.00    Monthly rent payment
  V2W3X4Y5    2024-05-12    Income     Freelance        +7,500.00    Mobile app UI design
  U1V2W3X4    2024-05-08    Expense    Food             -3,900.00    Grocery + restaurant
```

### Monthly Summary
```
  Month         Income          Expenses        Net
  ────────────────────────────────────────────────────────────
  2024-05       ₱  52,500.00    ₱  16,000.00    +₱  36,500.00
  2024-04       ₱  57,000.00    ₱  17,950.00    +₱  39,050.00
  2024-03       ₱  50,000.00    ₱  22,098.00    +₱  27,902.00
```

---

## 🎥 YouTube Demonstration
https://youtu.be/YEBVt2Gaj7Y?si=Ao6NMYIEyBFozFa0

## 📁 Data Storage

All data is automatically saved to `data/finance_data.json`. The file is created automatically on first run.

- **Transactions** are appended in real-time
- **Budgets** are updated immediately on change
- **Backups** are timestamped copies: `data/finance_data_backup_YYYYMMDD_HHMMSS.json`
- **CSV exports** land in: `data/transactions_YYYYMMDD_HHMMSS.csv`
- **TXT reports** land in: `data/summary_YYYYMMDD_HHMMSS.txt`

---

## 🧪 CLI Walkthrough Examples

### Example 1 — Full Transaction Cycle
```bash
# Start the app
python src/main.py

# Add an expense
→ 1 (Add Transaction) → expense → Food → 250 → "Mang Inasal dinner" → today → food

# View it
→ 2 (View Transactions) → 1 (All Transactions)

# Check budget impact
→ 5 (Budget Manager) → 2 (View Budget Status)

# Export to CSV
→ 6 (Export Data) → 1 (Export All Transactions)
```

### Example 2 — Monthly Analysis
```bash
# View March 2024 data
→ 3 (Search & Filter) → 3 (Filter by Month) → 2024 → 3

# View monthly trends
→ 4 (Reports & Analytics) → 3 (Monthly Summary)

# Export March report
→ 6 (Export Data) → 2 (Export Current Month)
```

---

## 👨‍💻 Author
Vincent Babia 
Intermediate Python Programming — Final Project
Section: BSCS-1B| School Year: 2025-2026

---

## 📄 License

This project is for academic and educational purposes.
