"""Single-page Streamlit chat interface for both assistant phases."""

import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

from data_access import get_all_parts
from phase1 import answer_question


PHASE_ONE = "Phase 1 — Rule Based"
PHASE_TWO = "Phase 2 — Gemini LLM"
API_BASE_URL = "http://127.0.0.1:8000"


def ask_phase_two(message, session_id):
    """Send one chat message to FastAPI and return the assistant reply."""
    request_body = json.dumps(
        {"message": message, "session_id": session_id}
    ).encode("utf-8")
    request = Request(
        f"{API_BASE_URL}/chat",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["reply"]
    except HTTPError as error:
        return f"FastAPI returned HTTP {error.code}. Check the backend terminal for details."
    except (URLError, TimeoutError):
        return (
            "Can't reach the Phase 2 backend. Start it with "
            "`python -m uvicorn backend:app --reload`, then try again."
        )
    except (KeyError, json.JSONDecodeError):
        return "FastAPI returned an unexpected response. Check the backend."


def render_app():
    """Build the chat page, phase selector, and live inventory panel."""
    st.set_page_config(
        page_title="CURT Inventory Assistant",
        page_icon="🏎️",
        layout="wide",
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    with st.sidebar:
        st.title("Parts inventory")
        try:
            inventory = get_all_parts()
            st.caption(f"{len(inventory)} parts · live SQLite data")
            st.dataframe(inventory, width="stretch", hide_index=True)
        except Exception:
            st.error("Couldn't load the inventory. Run the database seed command first.")

        st.divider()
        st.caption("Phase 2 needs FastAPI running in another terminal.")

    st.title("CURT Inventory Assistant")
    st.caption("Formula Student parts · stock, storage, and category questions")
    phase = st.selectbox(
        "Assistant mode",
        [PHASE_ONE, PHASE_TWO],
    )

    if not st.session_state.messages:
        st.info("Try: “How many brake pads do we have?”")

    prompt = st.chat_input("Ask a question about the inventory")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        if phase == PHASE_ONE:
            reply = answer_question(prompt)
        else:
            reply = ask_phase_two(prompt, st.session_state.session_id)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


if __name__ == "__main__":
    render_app()
