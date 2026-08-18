"""api.py — API 层"""
from db import get_items, add_item


def list_api():
    return {"items": get_items(), "count": len(get_items())}


def create_api(data):
    if not data or "name" not in data:
        raise ValueError("name is required")
    return add_item(data)