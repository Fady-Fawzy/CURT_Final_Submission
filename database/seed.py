"""Create the inventory table and add the starter parts."""

import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("curt_inventory.db")

STARTER_PARTS = [
    ("Brake Pads", 12, "Brakes", "Mechanical Workshop"),
    ("ECU", 1, "Electrical", "Electrical Cabinet"),
    ("Spark Plugs", 8, "Engine", "Engine Storage"),
    ("Wheel Nuts", 20, "Wheels", "Parts Cabinet"),
    ("Brake Fluid", 3, "Fluids", "Chemical Storage"),
    ("Steering Wheel", 1, "Cockpit", "Cockpit Shelf"),
    ("Suspension Spring", 4, "Suspension", "Suspension Rack"),
    ("Temperature Sensor", 2, "Electrical", "Electrical Cabinet"),
    ("Fuel Pump", 1, "Fuel System", "Fuel System Drawer"),
    ("Battery", 2, "Electrical", "Electrical Cabinet"),
    ("Oil Filter", 4, "Engine", "Engine Storage"),
    ("Drive Chain", 2, "Drivetrain", "Parts Cabinet"),
]


def initialize_database(database_path=DATABASE_PATH):
    """Create the table and insert starter parts without replacing stock counts."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS parts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    quantity INTEGER NOT NULL CHECK (quantity >= 0),
                    category TEXT NOT NULL,
                    location TEXT NOT NULL
                )
                """
            )
            existing_names = {
                row[0] for row in connection.execute("SELECT name FROM parts")
            }
            missing_parts = [
                part for part in STARTER_PARTS if part[0] not in existing_names
            ]
            connection.executemany(
                """
                INSERT INTO parts (name, quantity, category, location)
                VALUES (?, ?, ?, ?)
                """,
                missing_parts,
            )
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Inventory database is ready at: {DATABASE_PATH}")
