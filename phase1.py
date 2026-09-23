"""Rule-based inventory assistant for Phase 1."""

from difflib import get_close_matches

from data_access import get_all_parts, get_by_category, get_part


def _clean_name(text):
    """Remove punctuation and a simple article from an item or category name."""
    name = text.strip().strip(" ?.! ,")
    if name.startswith("the "):
        name = name[4:]
    return name.strip()


def _find_part(item_name):
    """Find an exact or partial item name, or return a helpful clarification."""
    if not item_name:
        return None, "Please include the item name, for example: 'How many brake pads do we have?'"

    part = get_part(item_name)
    if part is not None:
        return part, ""

    inventory = get_all_parts()
    partial_matches = [
        part for part in inventory if item_name.casefold() in part["name"].casefold()
    ]

    if len(partial_matches) == 1:
        part = partial_matches[0]
        return part, f"I matched '{item_name}' to {part['name']}. "

    if len(partial_matches) > 1:
        names = ", ".join(part["name"] for part in partial_matches)
        return None, f"I found multiple matching items: {names}. Please be more specific."

    item_names = [part["name"] for part in inventory]
    close_matches = get_close_matches(item_name, item_names, n=1, cutoff=0.65)
    if close_matches:
        part = get_part(close_matches[0])
        return part, f"I think you mean {part['name']}. "

    return None, f"I couldn't find '{item_name}' in the inventory. Please check the item name."


def answer_question(message):
    """Answer stock, location, and category questions using the inventory DB."""
    question = message.strip().lower()

    if "how many" in question:
        item_text = question.split("how many", 1)[1]
        item_text = item_text.split(" do we have", 1)[0]
        item_name = _clean_name(item_text)
        part, note = _find_part(item_name)
        if part is None:
            return note
        return f"{note}We have {part['quantity']} {part['name']}."

    if "where is" in question:
        item_text = question.split("where is", 1)[1]
        item_text = item_text.split(" stored", 1)[0]
        item_name = _clean_name(item_text)
        part, note = _find_part(item_name)
        if part is None:
            return note
        return f"{note}The {part['name']} is stored in {part['location']}."

    category_text = None
    if "list all items in" in question:
        category_text = question.split("list all items in", 1)[1]
    elif question.startswith("show me ") and question.rstrip(" ?.! ,").endswith(" items"):
        category_text = question[len("show me "):].rsplit(" items", 1)[0]

    if category_text is not None:
        category = _clean_name(category_text)
        parts = get_by_category(category)
        if not parts:
            return f"There are no items in the {category} category."

        item_list = ", ".join(
            f"{part['name']} ({part['quantity']})" for part in parts
        )
        return f"Items in {parts[0]['category']}: {item_list}."

    return "I can answer stock, storage-location, and category questions."
