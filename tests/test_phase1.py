import unittest

from phase1 import answer_question


class PhaseOneAssistantTests(unittest.TestCase):
    def test_answers_stock_question_from_inventory(self):
        answer = answer_question("How many brake pads do we have?")
        self.assertEqual(answer, "We have 12 Brake Pads.")

    def test_answers_location_question_from_inventory(self):
        answer = answer_question("Where is the ECU?")
        self.assertEqual(answer, "The ECU is stored in Electrical Cabinet.")

    def test_answers_location_question_that_says_stored(self):
        answer = answer_question("Where is ECU stored?")
        self.assertEqual(answer, "The ECU is stored in Electrical Cabinet.")

    def test_lists_parts_in_a_category(self):
        answer = answer_question("List all items in Electrical.")
        self.assertEqual(
            answer,
            "Items in Electrical: Battery (2), ECU (1), Temperature Sensor (2).",
        )

    def test_lists_parts_when_asked_to_show_category_items(self):
        answer = answer_question("Show me Electrical items.")
        self.assertEqual(
            answer,
            "Items in Electrical: Battery (2), ECU (1), Temperature Sensor (2).",
        )

    def test_explains_which_question_types_are_supported(self):
        answer = answer_question("Can you tell me about the inventory?")
        self.assertEqual(
            answer,
            "I can answer stock, storage-location, and category questions.",
        )

    def test_understands_a_unique_partial_item_name(self):
        answer = answer_question("How many brake pad do we have?")
        self.assertEqual(
            answer,
            "I matched 'brake pad' to Brake Pads. We have 12 Brake Pads.",
        )

    def test_suggests_a_match_for_a_small_spelling_mistake(self):
        answer = answer_question("How many brake pabs do we have?")
        self.assertEqual(
            answer,
            "I think you mean Brake Pads. We have 12 Brake Pads.",
        )

    def test_asks_for_the_item_when_it_is_missing(self):
        answer = answer_question("How many do we have?")
        self.assertEqual(
            answer,
            "Please include the item name, for example: 'How many brake pads do we have?'",
        )

    def test_asks_for_a_more_specific_name_when_partial_match_is_ambiguous(self):
        answer = answer_question("How many brake do we have?")
        self.assertEqual(
            answer,
            "I found multiple matching items: Brake Fluid, Brake Pads. Please be more specific.",
        )

    def test_reports_an_unknown_item(self):
        answer = answer_question("Where is the Turbo?")
        self.assertEqual(
            answer,
            "I couldn't find 'turbo' in the inventory. Please check the item name.",
        )


if __name__ == "__main__":
    unittest.main()
