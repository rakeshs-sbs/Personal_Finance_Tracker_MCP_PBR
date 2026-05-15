# 💸 Personal Finance Tracker — MCP Server

An MCP server that lets an LLM log, query, and analyse your personal
expenses stored in a local SQLite database (no external services needed).

---

## Prerequisites — Pop!_OS Setup

### 1. Install system dependencies

```bash
sudo apt update && sudo apt install -y \
    curl \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    python3-dev
```

> SQLite ships with Pop!_OS; the `libsqlite3-dev` package just adds the
> C headers in case any Python package needs to compile against it.

---

### 2. Install `uv` (Python package & project manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Reload your shell so `uv` is on `$PATH`:

```bash
source ~/.bashrc       # bash users
# or
source ~/.zshrc        # zsh users
```

Verify:

```bash
uv --version
# uv 0.x.x
```

---

### 3. Install ngrok (optional — only if you want a public URL)

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null

echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list

sudo apt update && sudo apt install -y ngrok
```

Sign up at <https://ngrok.com> (free) and authenticate:

```bash
ngrok config add-authtoken <YOUR_TOKEN>
```

---

## Project Setup

```bash
# 1. Enter the project folder
cd finance-mcp

# 2. Create .env from the template
cp .env.example .env

# 3. Install all Python dependencies + create virtual environment
uv sync
```

---

## Running the Server

```bash
uv run server.py
```

Expected output:

```
INFO     FastMCP server 'finance-tracker' running on http://127.0.0.1:8000
INFO     MCP endpoint: http://127.0.0.1:8000/mcp
```

---

## Connecting to Claude / an MCP Client

Add this block to your MCP client config (e.g. Claude Desktop's
`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "finance-tracker": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `log_expense(amount, category, note)` | Log a new expense to SQLite |
| `summarise_spending(period)` | Summary grouped by category |
| `budget_alert(category, limit)` | Check if you're over budget |
| `export_expenses(filename)` | Export all data to CSV |
| `list_recent_expenses(limit)` | Show the last N expenses |

---

## Test Prompts

```
"Log ₹450 for food — had lunch at the cafe."
"Log ₹1200 for transport — Uber rides this week."
"Show me my spending summary for this month."
"Am I over budget on food if my limit is ₹3000?"
"List my last 5 expenses."
"Export my expenses to a CSV file."
```

---

## Project Structure

```
finance-mcp/
├── .env              # local config — never commit
├── .env.example      # committed template
├── .gitignore
├── .python-version   # 3.12
├── pyproject.toml    # project metadata + deps
├── server.py         # MCP server + all tools
└── README.md
```

After first run, SQLite creates:

```
finance-mcp/
└── expenses.db       # your expense data (auto-created, gitignored)
```

---

## Common `uv` Commands

| Command | What it does |
|---------|-------------|
| `uv sync` | Install / update all deps from lock file |
| `uv add <pkg>` | Add a new dependency |
| `uv run server.py` | Run the server inside the managed venv |
| `uv run python` | Open a REPL inside the managed venv |
