# 💸 Personal Finance Tracker — MCP Server

A local **Model Context Protocol (MCP) server** that lets any MCP-compatible AI assistant (Claude, ChatGPT, etc.) log, query, and analyse your personal expenses through natural conversation — no cloud, no subscriptions, just a SQLite file on your machine.

---

## 📌 Project Overview

Instead of manually opening a spreadsheet every time you spend money, you simply tell your AI assistant:

> *"Log ₹450 for food — lunch at the cafe"*

The assistant calls your local MCP server, which writes the entry into a SQLite database. You can then ask for summaries, check if you're over budget, or export everything to CSV — all through chat.

```
You / AI Assistant
       │
       ▼  MCP (HTTP)
   server.py
       ├── log_expense()        → INSERT into SQLite
       ├── summarise_spending() → SELECT + aggregate by category
       ├── budget_alert()       → compare total vs your limit
       ├── export_expenses()    → dump all rows to CSV
       └── list_recent_expenses() → show last N entries
              │
              ▼
         expenses.db  (SQLite — lives on your machine)
```

---

## 🛠️ Tools & Technologies

| Tool / Library | Role |
|----------------|------|
| **Python 3.12** | Core language |
| **FastMCP** | Framework for building MCP servers; handles tool registration, HTTP transport, and the MCP protocol |
| **SQLite** | Lightweight, file-based database that stores all expense records locally — no server required |
| **httpx** | Async-capable HTTP client (FastMCP dependency) |
| **python-dotenv** | Loads `HOST` and `PORT` from a `.env` file at startup |
| **uv** | Fast Python package manager and project tool; replaces pip + venv in one command |
| **ngrok** | Tunnels your local server to a public HTTPS URL so remote AI clients (e.g. ChatGPT) can reach it |

---

## 📁 Project Structure

```
finance-mcp/
├── server.py          # MCP server — all 5 tools live here
├── pyproject.toml     # Project metadata and dependencies
├── .env.example       # Committed config template
├── .env               # Your local config (never commit this)
├── .python-version    # Pins Python to 3.12
├── .gitignore
└── README.md
```

After first run, SQLite automatically creates:

```
finance-mcp/
└── expenses.db        # Your expense data (auto-created, gitignored)
```

---

## ⚙️ Setup & Installation

### Prerequisites — Pop!_OS / Ubuntu

**1. Install system dependencies**

```bash
sudo apt update && sudo apt install -y \
    curl git build-essential \
    libssl-dev libsqlite3-dev libffi-dev python3-dev
```

**2. Install `uv`** (Python package & project manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc        # bash users
# or
source ~/.zshrc         # zsh users
```

Verify:

```bash
uv --version
```

**3. Install ngrok** *(optional — only needed for ChatGPT or remote clients)*

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null

echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list

sudo apt update && sudo apt install -y ngrok
```

Sign up at [ngrok.com](https://ngrok.com) (free) and authenticate:

```bash
ngrok config add-authtoken <YOUR_TOKEN>
```

---

### Project Setup

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/finance-mcp.git
cd finance-mcp
```

**2. Copy the environment template**

```bash
cp .env.example .env
```

The defaults work out of the box:

```
HOST=127.0.0.1
PORT=8000
```

**3. Install dependencies & create virtual environment**

```bash
uv sync
```

This reads `pyproject.toml`, creates `.venv/`, and installs everything in one step.

---

## 🚀 Running the Server

### Local (Claude Desktop / local clients)

```bash
uv run server.py
```

Expected output:

```
INFO     Started server process [XXXXX]
INFO     Application startup complete.
INFO     Uvicorn running on http://127.0.0.1:8000
```

Your MCP endpoint is now live at:

```
http://127.0.0.1:8000/mcp
```

### Public URL via ngrok (ChatGPT / remote clients)

Open a **second terminal** while the server is running:

```bash
ngrok http 8000
```

ngrok prints a public URL like:

```
Forwarding  https://abc123.ngrok-free.app -> http://127.0.0.1:8000
```

Your public MCP endpoint is:

```
https://abc123.ngrok-free.app/mcp
```

> ⚠️ Keep both terminals open. Closing either one stops the connection.

---

## 🔌 Connecting to an AI Client

### ChatGPT

1. Go to **Settings → Apps & Connectors → Advanced → Developer Mode → ON**
2. Navigate to **Settings → Apps & Connectors → Create**
3. Fill in:
   - **Name:** Finance Tracker
   - **Description:** Logs and analyses personal expenses
   - **URL:** `https://abc123.ngrok-free.app/mcp`
4. Click **Create**

---

## 🧰 Available Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `log_expense` | `amount`, `category`, `note?` | Log a new expense to the database |
| `summarise_spending` | `period?` | Spending grouped by category for a time period |
| `budget_alert` | `category`, `limit` | Check if you've exceeded your budget |
| `export_expenses` | `filename?` | Export all expenses to a CSV file |
| `list_recent_expenses` | `limit?` | Show the last N expense entries |

**Supported periods for `summarise_spending`:**
`today` · `this week` · `last week` · `this month` · `last month` · `all time`

---

## 💬 Example Prompts

```
"Log ₹450 for food — had lunch at the cafe."
"Log ₹1200 for transport — Uber rides this week."
"Show me my spending summary for this month."
"Am I over budget on food if my limit is ₹3000?"
"List my last 10 expenses."
"Export my expenses to a CSV file."
"How much did I spend last week in total?"
```

---

## 🔧 Common `uv` Commands

| Command | What it does |
|---------|-------------|
| `uv sync` | Install / update all deps from lock file |
| `uv add <pkg>` | Add a new dependency |
| `uv remove <pkg>` | Remove a dependency |
| `uv run server.py` | Run the server inside the managed venv |
| `uv run python` | Open a REPL inside the managed venv |

---

## 📄 License

MIT — free to use, modify, and distribute.
