"""todo_cli.py — 命令行待办清单工具（Task 3: 新增 stats 子命令）"""
import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save_todos(todos):
    with open(DATA_FILE, "w") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add(text):
    todos = load_todos()
    todos.append({"id": len(todos) + 1, "text": text, "done": False})
    save_todos(todos)
    print(f"added: {text}")


def list_todos():
    todos = load_todos()
    for t in todos:
        status = "[x]" if t["done"] else "[ ]"
        print(f"{t['id']:3d} {status} {t['text']}")


def done(todo_id):
    todos = load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            break
    save_todos(todos)
    print(f"done: #{todo_id}")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 todo_cli.py <add|list|done> [args]")
        return
    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 3:
        add(" ".join(sys.argv[2:]))
    elif cmd == "list":
        list_todos()
    elif cmd == "done" and len(sys.argv) >= 3:
        done(int(sys.argv[2]))
    else:
        print(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()