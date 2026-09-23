import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

from data_access import get_all_parts, get_by_category, get_part, update_quantity
from database.seed import initialize_database


class DataAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "test_inventory.db")
        initialize_database(self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_starts_with_at_least_ten_parts(self):
        self.assertGreaterEqual(len(get_all_parts(self.database_path)), 10)

    def test_reseeding_does_not_skip_ids_for_new_parts(self):
        initialize_database(self.database_path)
        with closing(sqlite3.connect(self.database_path)) as connection:
            cursor = connection.execute(
                "INSERT INTO parts (name, quantity, category, location) VALUES (?, ?, ?, ?)",
                ("New Test Part", 1, "Test", "Test Shelf"),
            )
            new_id = cursor.lastrowid
            connection.commit()

        self.assertEqual(new_id, len(get_all_parts(self.database_path)))

    def test_get_part_finds_name_without_case_mattering(self):
        part = get_part("brake pads", self.database_path)
        self.assertEqual(part["name"], "Brake Pads")
        self.assertEqual(part["quantity"], 12)

    def test_get_by_category_returns_matching_parts(self):
        parts = get_by_category("Electrical", self.database_path)
        self.assertTrue(parts)
        self.assertTrue(all(part["category"] == "Electrical" for part in parts))

    def test_update_quantity_changes_the_database_value(self):
        updated_part = update_quantity("Brake Pads", -2, self.database_path)
        self.assertEqual(updated_part["quantity"], 10)

    def test_get_part_returns_none_for_unknown_name(self):
        self.assertIsNone(get_part("Unlisted Part", self.database_path))


if __name__ == "__main__":
    unittest.main()
