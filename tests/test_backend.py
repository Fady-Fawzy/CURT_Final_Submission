import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import _run_requested_tool, app, sessions
from database.seed import initialize_database


class BackendEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()
        cls.client = TestClient(app)

    def setUp(self):
        sessions.clear()

    def test_get_inventory_returns_current_parts_as_json(self):
        response = self.client.get("/inventory")

        self.assertEqual(response.status_code, 200)
        inventory = response.json()
        self.assertGreaterEqual(len(inventory), 10)
        self.assertEqual(inventory[0]["name"], "Battery")

    @patch("backend.create_gemini_client")
    def test_post_chat_executes_requested_tool_then_returns_gemini_reply(self, make_client):
        function_call = SimpleNamespace(
            name="check_stock", args={"item_name": "Brake Pads"}, id="call-123"
        )
        first_response = SimpleNamespace(
            function_calls=[function_call],
            candidates=[SimpleNamespace(content="model tool-call content")],
            text=None,
        )
        final_response = SimpleNamespace(function_calls=None, text="We have 12 Brake Pads.")
        client = SimpleNamespace()
        client.models = SimpleNamespace(
            generate_content=Mock(
                side_effect=[first_response, final_response]
            )
        )
        make_client.return_value = client

        with patch("builtins.print") as debug_print:
            response = self.client.post(
                "/chat",
                json={"message": "How many brake pads do we have?", "session_id": "test-session"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "We have 12 Brake Pads."})
        debug_print.assert_any_call("Gemini requested tool: check_stock")
        self.assertEqual(client.models.generate_content.call_count, 2)
        follow_up_contents = client.models.generate_content.call_args_list[1].kwargs[
            "contents"
        ]
        self.assertEqual(follow_up_contents[-1].role, "tool")
        tool_result = follow_up_contents[-1].parts[0].function_response.response
        self.assertEqual(follow_up_contents[-1].parts[0].function_response.id, "call-123")
        self.assertEqual(
            tool_result["result"],
            {
                "found": True,
                "item_name": "Brake Pads",
                "quantity": 12,
                "location": "Mechanical Workshop",
            },
        )

    @patch("backend.create_gemini_client")
    def test_post_chat_returns_gemini_text_when_no_tool_is_needed(self, make_client):
        response_from_gemini = SimpleNamespace(
            function_calls=None,
            text="Please ask me about a CURT inventory item.",
        )
        client = SimpleNamespace()
        client.models = SimpleNamespace(
            generate_content=Mock(return_value=response_from_gemini)
        )
        make_client.return_value = client

        response = self.client.post(
            "/chat",
            json={"message": "Hello", "session_id": "test-session"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"reply": "Please ask me about a CURT inventory item."}
        )
        client.models.generate_content.assert_called_once()

    @patch("backend.create_gemini_client")
    def test_follow_up_message_receives_earlier_session_messages(self, make_client):
        first_tool_call = SimpleNamespace(
            name="check_stock", args={"item_name": "Brake Pads"}, id="call-first"
        )
        follow_up_tool_call = SimpleNamespace(
            name="check_stock", args={"item_name": "Brake Pads"}, id="call-follow-up"
        )
        responses = [
            SimpleNamespace(
                function_calls=[first_tool_call],
                candidates=[SimpleNamespace(content="first model tool call")],
                text=None,
            ),
            SimpleNamespace(function_calls=None, text="We have 12 Brake Pads."),
            SimpleNamespace(
                function_calls=[follow_up_tool_call],
                candidates=[SimpleNamespace(content="follow-up model tool call")],
                text=None,
            ),
            SimpleNamespace(
                function_calls=None,
                text="They are stored in the Mechanical Workshop.",
            ),
        ]
        client = SimpleNamespace()
        client.models = SimpleNamespace(generate_content=Mock(side_effect=responses))
        make_client.return_value = client

        first_reply = self.client.post(
            "/chat",
            json={"message": "How many brake pads do we have?", "session_id": "chat-a"},
        )
        follow_up_reply = self.client.post(
            "/chat",
            json={"message": "Where are they stored?", "session_id": "chat-a"},
        )

        self.assertEqual(first_reply.json()["reply"], "We have 12 Brake Pads.")
        self.assertEqual(
            follow_up_reply.json()["reply"],
            "They are stored in the Mechanical Workshop.",
        )
        second_request_contents = client.models.generate_content.call_args_list[2].kwargs[
            "contents"
        ]
        self.assertEqual(
            [
                (message.role, message.parts[0].text)
                for message in second_request_contents[:3]
            ],
            [
                ("user", "How many brake pads do we have?"),
                ("model", "We have 12 Brake Pads."),
                ("user", "Where are they stored?"),
            ],
        )

    @patch("backend.create_gemini_client")
    def test_different_session_ids_do_not_share_conversation_history(self, make_client):
        responses = [
            SimpleNamespace(function_calls=None, text="We have 12 Brake Pads."),
            SimpleNamespace(function_calls=None, text="Please name an item."),
        ]
        client = SimpleNamespace()
        client.models = SimpleNamespace(generate_content=Mock(side_effect=responses))
        make_client.return_value = client

        self.client.post(
            "/chat",
            json={"message": "How many brake pads do we have?", "session_id": "chat-a"},
        )
        self.client.post(
            "/chat",
            json={"message": "Where are they stored?", "session_id": "chat-b"},
        )

        second_request_contents = client.models.generate_content.call_args_list[1].kwargs[
            "contents"
        ]
        self.assertEqual(len(second_request_contents), 1)
        self.assertEqual(second_request_contents[0].parts[0].text, "Where are they stored?")

    def test_post_chat_requires_message_and_session_id(self):
        response = self.client.post("/chat", json={"message": "Hello"})

        self.assertEqual(response.status_code, 422)

    @patch("backend.create_gemini_client")
    def test_post_chat_rejects_blank_message(self, make_client):
        make_client.return_value.models.generate_content.return_value = SimpleNamespace(
            function_calls=None, text="Unexpected reply"
        )

        for message in ("", "   "):
            with self.subTest(message=message):
                response = self.client.post(
                    "/chat", json={"message": message, "session_id": "chat-a"}
                )
                self.assertEqual(response.status_code, 422)
        self.assertEqual(sessions, {})

    @patch("backend.create_gemini_client")
    def test_post_chat_rejects_blank_session_id(self, make_client):
        make_client.return_value.models.generate_content.return_value = SimpleNamespace(
            function_calls=None, text="Unexpected reply"
        )

        for session_id in ("", "   "):
            with self.subTest(session_id=session_id):
                response = self.client.post(
                    "/chat", json={"message": "Hello", "session_id": session_id}
                )
                self.assertEqual(response.status_code, 422)
        self.assertEqual(sessions, {})

    @patch("backend.create_gemini_client")
    def test_post_chat_reports_missing_key_without_internal_details(self, make_client):
        make_client.side_effect = RuntimeError(
            "GEMINI_API_KEY is missing; diagnostic-token-not-for-response"
        )
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/chat", json={"message": "Hello", "session_id": "chat-a"}
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])
        self.assertNotIn("diagnostic-token", response.text)
        self.assertEqual(sessions, {})

    @patch("backend.create_gemini_client")
    def test_post_chat_reports_provider_error_without_internal_details(self, make_client):
        make_client.return_value.models.generate_content.side_effect = RuntimeError(
            "private-provider-diagnostic"
        )
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/chat", json={"message": "Hello", "session_id": "chat-a"}
        )

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private-provider-diagnostic", response.text)
        self.assertEqual(sessions, {})

    def test_malformed_tool_argument_returns_error_instead_of_raising(self):
        function_call = SimpleNamespace(name="check_stock", args={"item_name": 123})

        result = _run_requested_tool(function_call)

        self.assertEqual(result, {"error": "The tool request had invalid arguments."})


if __name__ == "__main__":
    unittest.main()
