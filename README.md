# CURT Inventory Assistant

A Formula Student parts assistant with two modes: a rule-based assistant and a Gemini-powered assistant. Both read the same SQLite inventory, so the answers come from one source of data.

## Overview

Phase 1 answers common stock, storage-location, and category questions using Python rules. Phase 2 sends the conversation to a FastAPI backend, which can ask Gemini for an approved inventory tool call. The backend runs that tool and returns the result to Gemini to write a reply. Gemini does not access SQLite directly.

The project folder includes `database/curt_inventory.db`, already initialized with 12 sample parts. You can also run the seed command to create the database if it is missing or add any missing starter parts.

## Features

- Switch between rule-based Phase 1 and Gemini Phase 2 in the Streamlit app.
- View current inventory from the same SQLite database used by both modes.
- Ask about stock quantities, storage locations, and category contents.
- Handle missing, unknown, ambiguous, and slightly misspelled item names in Phase 1.
- Keep short conversation history per session in the Phase 2 backend.
- Restrict Gemini tool requests to three declared backend functions.

## Architecture

```text
Phase 1: Streamlit → phase1.py → data_access.py → SQLite

Phase 2: Streamlit → FastAPI → Gemini
                              ↕ approved tool requests
                        backend tools → data_access.py → same SQLite
```

The Streamlit app provides the chat and inventory table. Phase 1 calls local Python rules. Phase 2 posts the user's message and session ID to FastAPI. Gemini can request a declared tool; FastAPI checks the function name and arguments, runs the matching Python function, and sends its result to Gemini. The `data_access.py` module contains the SQLite queries.

## Tech Stack

- Python 3.10 or newer
- Streamlit
- FastAPI and Uvicorn
- SQLite
- Google GenAI Python SDK (`google-genai`), using model `gemini-3.8-flash`
- `python-dotenv` for loading the local environment file

## Project Structure

```text
app.py                       Streamlit chat, mode selector, and inventory table
backend.py                   FastAPI endpoints, Gemini requests, tool checks, sessions
phase1.py                    Rule-based replies and item-name matching
tools.py                     Approved inventory functions and Gemini declarations
data_access.py               SQLite read and update functions
gemini_client.py             Gemini model name and API-key loading
database/curt_inventory.db   Bundled, pre-seeded 12-part SQLite inventory
database/seed.py             Creates the table and inserts missing starter parts
.env.example                 Empty template for the Gemini API key
requirements.txt             Python package list
tests/                       Unit tests and Streamlit page checks
REFLECTION.md                Short project reflection
```

## Installation

Open PowerShell in the project folder. Create and activate a virtual environment, then install the listed packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, open a new terminal or use the virtual environment's Python directly with `\.venv\Scripts\python.exe -m ...`.

## Environment Variables

Only Phase 2 needs a Gemini API key. Copy `.env.example` to `.env` and put your key in the value:

```text
GEMINI_API_KEY=your_key_goes_here
```

The app loads `.env` locally. Keep the real key private; `.env` is ignored by Git. Do not put a real key in source code, screenshots, or `.env.example`. Phase 1 does not need a key.

## Database Setup

The repository includes a pre-seeded database at `database/curt_inventory.db` with 12 sample parts. From the project folder, you may initialize it with:

```powershell
python -m database.seed
```

This creates the `parts` table if needed and inserts starter rows that are missing. It does not replace existing rows or reset quantities. The database contains part name, quantity, category, and location. The quantity must be zero or greater.

## Start Backend

Activate the virtual environment in one PowerShell terminal, then run:

```powershell
python -m uvicorn backend:app --reload
```

FastAPI listens at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for its interactive API documentation. Leave this terminal running while using Phase 2.

## Start Streamlit

Open a second PowerShell terminal in the project folder, activate the virtual environment, then run:

```powershell
python -m streamlit run app.py
```

Streamlit prints the local app address in the terminal. Phase 1 can be used without the backend. Phase 2 requires the backend and a valid `GEMINI_API_KEY` in `.env`.

## API Documentation

### `POST /chat`

Request JSON:

```json
{
  "message": "How many brake pads do we have?",
  "session_id": "demo-session"
}
```

Both fields must contain non-blank strings. The response is:

```json
{
  "reply": "..."
}
```

### `GET /inventory`

Returns the current inventory as a JSON list. Each part has `id`, `name`, `quantity`, `category`, and `location` fields.

## Tool Calling

Gemini receives declarations for these backend functions:

- `check_stock(item_name)` returns whether the part exists and, when found, its quantity and location.
- `list_by_category(category)` returns the matching inventory rows.
- `flag_shortage(item_name)` prints a low-stock note and returns a logged result. It does not change the quantity or send an alert.

Automatic function execution is disabled in the Gemini client configuration. FastAPI checks requested tool names against `AVAILABLE_TOOLS` and validates the arguments before calling a function. Inventory reads go through `data_access.py`; Gemini cannot issue SQL.

## Conversation Memory

Streamlit creates a session ID for its chat session and sends it with each Phase 2 message. FastAPI stores user and assistant text in an in-memory Python dictionary keyed by that ID. Gemini receives earlier messages from the same session, so a follow-up such as “Where are they stored?” can use the previous question's context. Different IDs keep separate histories. This history is temporary and is cleared when FastAPI restarts; it is not stored in SQLite.

## Edge Cases

Phase 1 uses simple keyword rules for stock, location, and category questions. It can use a unique partial item-name match, suggest a close match for a small spelling mistake, ask for a more specific name when a partial match is ambiguous, and explain when a part is missing or unknown. For example:

| Question | Expected behavior |
| --- | --- |
| How many brake pads do we have? | Gives the current Brake Pads quantity. |
| Where is the ECU? | Gives the ECU storage location. |
| Show me Electrical items. | Lists the matching category items. |
| How many do we have? | Asks for the item name. |
| Where is the turbo? | Says the item was not found. |

Phase 2 validates non-blank request fields and tool arguments. If the Gemini key is missing, the backend responds with a configuration error. Provider or unexpected backend errors are returned as a general assistant error rather than exposing internal details.

## Testing

With the virtual environment active, run the test suite from the project folder:

```powershell
python -m unittest discover -s tests -v
```

The tests cover database access, Phase 1 answers and edge cases, Gemini client configuration, approved tools and argument validation, API routes and session history, and the Streamlit page behavior. Gemini API calls in backend tests are mocked, so a passing test run does not prove live Gemini connectivity.

## Limitations

- Phase 1 understands a limited set of question patterns and uses basic name matching.
- Phase 2 needs internet access and a working Gemini API key; service availability or quotas may affect it.
- Conversation history exists only in backend memory and is lost at restart.
- The shortage tool only prints a note; it does not notify a person or update stock.
- The inventory is a small sample database. Although a quantity update function exists, the chat interface does not provide inventory editing.
- Railway deployment is optional and is not configured in this project.

## Reflection

See [REFLECTION.md](REFLECTION.md) for the short project reflection.

