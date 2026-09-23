import os
import unittest
from unittest.mock import patch

from gemini_client import MODEL_NAME, create_gemini_client


class GeminiClientTests(unittest.TestCase):
    def test_missing_api_key_has_a_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
                create_gemini_client()

    def test_api_key_is_passed_to_the_google_client(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
            with patch("gemini_client.genai.Client") as mock_client:
                create_gemini_client()

        mock_client.assert_called_once_with(api_key="test-key")

    def test_model_name_is_a_gemini_model_id(self):
        self.assertEqual(MODEL_NAME, "gemini-3.8-flash")


if __name__ == "__main__":
    unittest.main()
