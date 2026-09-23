"""Approved inventory functions that the Phase 2 backend can execute."""

from data_access import get_by_category, get_part
from google.genai import types


def check_stock(item_name):
    """Return a part's quantity and storage location."""
    part = get_part(item_name)
    if part is None:
        return {
            "found": False,
            "message": f"The item '{item_name}' was not found in the inventory.",
        }

    return {
        "found": True,
        "item_name": part["name"],
        "quantity": part["quantity"],
        "location": part["location"],
    }


def list_by_category(category):
    """Return all inventory parts in the requested category."""
    return get_by_category(category)


def flag_shortage(item_name):
    """Print a simple low-stock note for a part."""
    print(f"LOW STOCK FLAG: {item_name}")
    return {"logged": True, "item_name": item_name}


# Only functions in this dictionary are available for future model requests.
AVAILABLE_TOOLS = {
    "check_stock": check_stock,
    "list_by_category": list_by_category,
    "flag_shortage": flag_shortage,
}


GEMINI_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="check_stock",
            description="Get the quantity and storage location for one inventory item.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The inventory part name, such as Brake Pads.",
                    }
                },
                "required": ["item_name"],
            },
        ),
        types.FunctionDeclaration(
            name="list_by_category",
            description="List the inventory items in one category.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "The inventory category, such as Electrical.",
                    }
                },
                "required": ["category"],
            },
        ),
        types.FunctionDeclaration(
            name="flag_shortage",
            description="Log a low-stock flag when the user asks to flag or report a shortage.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The inventory part name with a shortage.",
                    }
                },
                "required": ["item_name"],
            },
        ),
    ]
)
