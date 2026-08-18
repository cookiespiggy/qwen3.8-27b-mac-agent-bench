"""db.py — 内存数据存储"""
_items = [
    {"id": 1, "name": "apple", "price": 3.5},
    {"id": 2, "name": "banana", "price": 2.0},
]


def get_items():
    return list(_items)


def add_item(item):
    item = dict(item)
    item["id"] = max([i["id"] for i in _items], default=0) + 1
    _items.append(item)
    return item