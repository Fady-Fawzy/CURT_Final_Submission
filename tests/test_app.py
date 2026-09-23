import json
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

from app import ask_phase_two
from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_page_shows_phase_selector_inventory_and_chat_input(self):
        app_test = AppTest.from_file(
            Path(__file__).parent.parent / "app.py", default_timeout=10
        ).run()

        self.assertFalse(app_test.exception)
        self.assertEqual(app_test.selectbox[0].label, "Assistant mode")
        self.assertEqual(
            app_test.chat_input[0].placeholder,
            "Ask a question about the inventory",
        )
        self.assertTrue(app_test.dataframe)

    def test_phase_one_chat_displays_answer_from_inventory(self):
        app_test = AppTest.from_file(
            Path(__file__).parent.parent / "app.py", default_timeout=10
        ).run()
        app_test.chat_input[0].set_value("How many brake pads do we have?").run()

        displayed_text = [element.value for element in app_test.markdown]
        self.assertIn("We have 12 Brake Pads.", displayed_text)

    def test_phase_selector_can_switch_without_restarting_page(self):
        app_test = AppTest.from_file(
            Path(__file__).parent.parent / "app.py", default_timeout=10
        ).run()
        app_test.selectbox[0].select("Phase 2 — Gemini LLM").run()

        self.assertEqual(app_test.selectbox[0].value, "Phase 2 — Gemini LLM")

    def test_phase_two_helper_posts_message_and_session_id(self):
        response = type("Response", (), {
            "read": lambda self: b'{"reply":"The ECU is in the Electrical Cabinet."}',
            "__enter__": lambda self: self,
            "__exit__": lambda self, *args: None,
        })()

        with patch("app.urlopen", return_value=response) as mock_urlopen:
            reply = ask_phase_two("Where is the ECU?", "session-123")

        self.assertEqual(reply, "The ECU is in the Electrical Cabinet.")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            json.loads(request.data),
            {"message": "Where is the ECU?", "session_id": "session-123"},
        )

    def test_phase_two_chat_displays_backend_reply(self):
        reply = BytesIO(b'{"reply":"The ECU is in the Electrical Cabinet."}')
        with patch("urllib.request.urlopen", return_value=reply) as post:
            app_test = AppTest.from_file(
                Path(__file__).parent.parent / "app.py", default_timeout=10
            ).run()
            app_test.selectbox[0].select("Phase 2 — Gemini LLM").run()
            app_test.chat_input[0].set_value("Where is the ECU?").run()

        self.assertFalse(app_test.exception)
        self.assertIn(
            "The ECU is in the Electrical Cabinet.",
            [element.value for element in app_test.markdown],
        )
        request = post.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8000/chat")
        self.assertEqual(json.loads(request.data)["message"], "Where is the ECU?")
        self.assertTrue(json.loads(request.data)["session_id"])

    def test_phase_two_connection_failure_shows_start_command(self):
        with patch("urllib.request.urlopen", side_effect=URLError("connection refused")):
            app_test = AppTest.from_file(
                Path(__file__).parent.parent / "app.py", default_timeout=10
            ).run()
            app_test.selectbox[0].select("Phase 2 — Gemini LLM").run()
            app_test.chat_input[0].set_value("How many brake pads do we have?").run()

        self.assertFalse(app_test.exception)
        self.assertTrue(
            any(
                "python -m uvicorn backend:app --reload" in element.value
                for element in app_test.markdown
            )
        )


if __name__ == "__main__":
    unittest.main()
