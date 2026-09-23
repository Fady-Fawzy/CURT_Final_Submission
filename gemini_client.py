"""Load Gemini configuration and create a client when a key is available."""

import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

MODEL_NAME = "gemini-3.8-flash"


def create_gemini_client():
    """Create the Google GenAI client using GEMINI_API_KEY from the environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your key to the local .env file."
        )

    return genai.Client(api_key=api_key)
