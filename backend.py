"""FastAPI backend for the CURT inventory assistant."""

from fastapi import FastAPI, HTTPException
from google.genai import types
from pydantic import BaseModel, field_validator

from data_access import get_all_parts
from gemini_client import MODEL_NAME, create_gemini_client
from tools import AVAILABLE_TOOLS, GEMINI_TOOL


app = FastAPI(title="CURT Inventory Assistant")

# Each key holds a short list of messages for that conversation.
sessions = {}


class ChatRequest(BaseModel):
    """The message and conversation ID sent to the chat endpoint."""

    message: str
    session_id: str

    @field_validator("message", "session_id")
    @classmethod
    def must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("This field must not be blank.")
        return value.strip()


class ChatResponse(BaseModel):
    """The assistant's reply returned by the chat endpoint."""

    reply: str


def _run_requested_tool(function_call):
    """Run a model-requested function only if it is in our allowlist."""
    tool_function = AVAILABLE_TOOLS.get(function_call.name)
    if tool_function is None:
        return {"error": "That tool is not available."}

    argument_name = "category" if function_call.name == "list_by_category" else "item_name"
    arguments = function_call.args or {}
    if (
        not isinstance(arguments, dict)
        or set(arguments) != {argument_name}
        or not isinstance(arguments[argument_name], str)
        or not arguments[argument_name].strip()
    ):
        return {"error": "The tool request had invalid arguments."}

    try:
        return tool_function(**arguments)
    except TypeError:
        return {"error": "The tool request had invalid arguments."}


def _answer_with_gemini(message, session_id):
    """Ask Gemini, execute approved tool calls in the backend, then get a reply."""
    try:
        client = create_gemini_client()
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured. Set GEMINI_API_KEY in the local .env file.",
        ) from error
    contents = []
    for saved_message in sessions.get(session_id, []):
        role = "user" if saved_message["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=saved_message["content"])],
            )
        )
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )
    )
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are the CURT inventory assistant. Use tools for inventory facts. "
            "Never guess quantities, locations, or category contents. Use flag_shortage "
            "only when the user asks to report or flag a shortage."
        ),
        tools=[GEMINI_TOOL],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=config,
    )

    # A tool may lead to another tool request, so allow a few short rounds.
    reply = None
    for _ in range(3):
        function_calls = response.function_calls or []
        if not function_calls:
            reply = response.text or "I couldn't create a reply for that question."
            break

        contents.append(response.candidates[0].content)
        tool_parts = []
        for function_call in function_calls:
            print(f"Gemini requested tool: {function_call.name}")
            result = _run_requested_tool(function_call)
            tool_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=function_call.name,
                        response={"result": result},
                        id=function_call.id,
                    )
                )
            )
        contents.append(types.Content(role="tool", parts=tool_parts))

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )

    if reply is None:
        reply = response.text or "I couldn't finish processing that question."

    messages = sessions.setdefault(session_id, [])
    messages.append({"role": "user", "content": message})
    messages.append({"role": "assistant", "content": reply})
    return reply


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Answer a chat message using Gemini and approved inventory tools."""
    try:
        reply = _answer_with_gemini(request.message, request.session_id)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="The assistant could not complete the request. Please try again later.",
        ) from error
    return ChatResponse(reply=reply)


@app.get("/inventory")
def inventory():
    """Return the current inventory as a JSON list."""
    return get_all_parts()
