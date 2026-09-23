"""Small functions for reading and updating the SQLite inventory."""

import sqlite3

from database.seed import DATABASE_PATH


def _connect(database_path):
    """Open the database and return rows with column names."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _row_to_dict(row):
    """Convert a database row to a regular Python dictionary."""
    if row is None:
        return None
    return dict(row)


def get_part(name, database_path=DATABASE_PATH):
    """Find one part by name, without requiring matching letter case."""
    connection = _connect(database_path)
    try:
        row = connection.execute(
            "SELECT * FROM parts WHERE LOWER(name) = LOWER(?)",
            (name.strip(),),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        connection.close()


def get_by_category(category, database_path=DATABASE_PATH):
    """Return all parts in a category, without requiring matching letter case."""
    connection = _connect(database_path)
    try:
        rows = connection.execute(
            "SELECT * FROM parts WHERE LOWER(category) = LOWER(?) ORDER BY name",
            (category.strip(),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_all_parts(database_path=DATABASE_PATH):
    """Return the current inventory, sorted by part name."""
    connection = _connect(database_path)
    try:
        rows = connection.execute("SELECT * FROM parts ORDER BY name").fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def update_quantity(name, delta, database_path=DATABASE_PATH):
    """Add delta to a part's quantity and return the updated part."""
    part = get_part(name, database_path)
    if part is None:
        return None

    new_quantity = part["quantity"] + delta
    if new_quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    connection = _connect(database_path)
    try:
        connection.execute(
            "UPDATE parts SET quantity = ? WHERE id = ?",
            (new_quantity, part["id"]),
        )
        connection.commit()
    finally:
        connection.close()

    return get_part(name, database_path)
