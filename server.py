import os
import sqlite3
import csv
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

_host = os.environ.get("HOST", "127.0.0.1")
_port = int(os.environ.get("PORT", "8000"))
DB_PATH = Path(__file__).parent / "expenses.db"

mcp = FastMCP(
    "finance-tracker",
    host=_host,
    port=_port,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating it if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            amount    REAL    NOT NULL,
            category  TEXT    NOT NULL,
            note      TEXT    DEFAULT '',
            logged_at TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def log_expense(amount: float, category: str, note: str = "") -> str:
    """
    Log a new expense into the database.

    Args:
        amount:   Amount in ₹ (e.g. 450.0).
        category: Spending category such as food, transport, shopping, etc.
        note:     Optional short description of the expense.

    Returns:
        Confirmation message with the logged details.
    """
    if amount <= 0:
        return "❌ Amount must be greater than zero."

    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO expenses (amount, category, note, logged_at) VALUES (?, ?, ?, ?)",
            (amount, category.lower().strip(), note.strip(), now),
        )

    return (
        f"✅ Logged ₹{amount:.2f} under '{category}'"
        + (f" — {note}" if note else "")
        + f" at {now}."
    )


@mcp.tool()
def summarise_spending(period: str = "this month") -> str:
    """
    Return a spending summary grouped by category for a given period.

    Args:
        period: One of 'today', 'this week', 'this month', 'last month',
                'last week', or 'all time'. Defaults to 'this month'.

    Returns:
        A formatted text summary of spending by category and total.
    """
    today = date.today()

    if period == "today":
        start = today.isoformat()
        label = "Today"
    elif period in ("this week", "last week"):
        # ISO week: Monday = day 0
        day_of_week = today.weekday()
        week_start = today.replace(day=today.day - day_of_week)
        if period == "last week":
            week_start = week_start.replace(day=week_start.day - 7)
        start = week_start.isoformat()
        label = period.title()
    elif period == "last month":
        if today.month == 1:
            start = date(today.year - 1, 12, 1).isoformat()
        else:
            start = date(today.year, today.month - 1, 1).isoformat()
        label = "Last Month"
    elif period == "all time":
        start = "1970-01-01"
        label = "All Time"
    else:  # default: this month
        start = date(today.year, today.month, 1).isoformat()
        label = "This Month"

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT category, SUM(amount) as total, COUNT(*) as txn_count
            FROM expenses
            WHERE date(logged_at) >= ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (start,),
        ).fetchall()

    if not rows:
        return f"No expenses recorded for {label}."

    lines = [f"📊 Spending Summary — {label}", ""]
    grand_total = 0.0
    for row in rows:
        lines.append(f"  {row['category'].capitalize():<15} ₹{row['total']:>8.2f}  ({row['txn_count']} txn)")
        grand_total += row["total"]
    lines += ["", f"  {'TOTAL':<15} ₹{grand_total:>8.2f}"]
    return "\n".join(lines)


@mcp.tool()
def budget_alert(category: str, limit: float) -> str:
    """
    Check whether spending in a category this month exceeds a given limit.

    Args:
        category: The expense category to check (e.g. 'food').
        limit:    Monthly budget limit in ₹.

    Returns:
        A message indicating whether the budget is safe or breached.
    """
    start = date.today().replace(day=1).isoformat()
    cat = category.lower().strip()

    with get_db() as conn:
        row = conn.execute(
            "SELECT SUM(amount) as total FROM expenses WHERE category = ? AND date(logged_at) >= ?",
            (cat, start),
        ).fetchone()

    total = row["total"] or 0.0
    remaining = limit - total
    pct = (total / limit * 100) if limit > 0 else 0

    if total == 0:
        return f"✅ No spending recorded for '{category}' this month. Budget: ₹{limit:.2f}"
    elif total >= limit:
        return (
            f"🚨 OVER BUDGET on '{category}'!\n"
            f"   Spent:  ₹{total:.2f}\n"
            f"   Limit:  ₹{limit:.2f}\n"
            f"   Over by ₹{abs(remaining):.2f} ({pct:.0f}% used)"
        )
    else:
        return (
            f"{'⚠️ ' if pct >= 80 else '✅ '} '{category.capitalize()}' budget status:\n"
            f"   Spent:     ₹{total:.2f}\n"
            f"   Limit:     ₹{limit:.2f}\n"
            f"   Remaining: ₹{remaining:.2f} ({pct:.0f}% used)"
        )


@mcp.tool()
def export_expenses(filename: str = "expenses_export.csv") -> str:
    """
    Export all expenses to a CSV file in the project directory.

    Args:
        filename: Name of the CSV file to create (default: expenses_export.csv).

    Returns:
        Path of the created file and the number of rows exported.
    """
    out_path = Path(__file__).parent / filename
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, amount, category, note, logged_at FROM expenses ORDER BY logged_at"
        ).fetchall()

    if not rows:
        return "No expenses to export."

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "amount", "category", "note", "logged_at"])
        for row in rows:
            writer.writerow([row["id"], row["amount"], row["category"], row["note"], row["logged_at"]])

    return f"✅ Exported {len(rows)} rows to {out_path}"


@mcp.tool()
def list_recent_expenses(limit: int = 10) -> str:
    """
    List the most recent expense entries.

    Args:
        limit: Number of recent entries to show (default: 10).

    Returns:
        A formatted list of recent expenses.
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT amount, category, note, logged_at FROM expenses ORDER BY logged_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    if not rows:
        return "No expenses logged yet."

    lines = [f"🧾 Last {limit} Expenses", ""]
    for row in rows:
        note_str = f" — {row['note']}" if row['note'] else ""
        lines.append(f"  ₹{row['amount']:>8.2f}  [{row['category']}]{note_str}  ({row['logged_at'][:10]})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
