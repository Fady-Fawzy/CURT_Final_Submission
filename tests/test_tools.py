import io
import unittest
from contextlib import redirect_stdout

from tools import AVAILABLE_TOOLS, check_stock, flag_shortage, list_by_category


class InventoryToolTests(unittest.TestCase):
    def test_check_stock_returns_quantity_and_location(self):
        result = check_stock("brake pads")

        self.assertEqual(
            result,
            {
                "found": True,
                "item_name": "Brake Pads",
                "quantity": 12,
                "location": "Mechanical Workshop",
            },
        )

    def test_check_stock_reports_an_unknown_item(self):
        result = check_stock("Unlisted Part")

        self.assertEqual(result["found"], False)
        self.assertIn("Unlisted Part", result["message"])

    def test_list_by_category_returns_matching_parts(self):
        results = list_by_category("Electrical")

        self.assertEqual(
            [part["name"] for part in results],
            ["Battery", "ECU", "Temperature Sensor"],
        )

    def test_flag_shortage_logs_the_part_name(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = flag_shortage("Brake Pads")

        self.assertEqual(result, {"logged": True, "item_name": "Brake Pads"})
        self.assertEqual(output.getvalue().strip(), "LOW STOCK FLAG: Brake Pads")

    def test_available_tools_only_contains_the_approved_functions(self):
        self.assertEqual(
            set(AVAILABLE_TOOLS),
            {"check_stock", "list_by_category", "flag_shortage"},
        )


if __name__ == "__main__":
    unittest.main()
