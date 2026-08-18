"""test_todo.py — todo_cli 测试（Task 3 新增 stats 后需全部通过）"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import todo_cli

DATA_FILE = todo_cli.DATA_FILE


def setup_function():
    todo_cli.save_todos([])


def teardown_function():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)


def make_fixture():
    todo_cli.save_todos([
        {"id": 1, "text": "buy milk", "done": True},
        {"id": 2, "text": "write report", "done": False},
        {"id": 3, "text": "call mom", "done": False},
        {"id": 4, "text": "walk dog", "done": True},
    ])


def test_add():
    todo_cli.add("hello")
    todos = todo_cli.load_todos()
    assert len(todos) == 1
    assert todos[0]["text"] == "hello"
    assert todos[0]["done"] is False


def test_done():
    make_fixture()
    todo_cli.done(2)
    todos = todo_cli.load_todos()
    assert todos[1]["done"] is True


def test_stats_function_exists():
    """stats 子命令必须是真实函数，调用后返回可 JSON 序列化的结果"""
    assert hasattr(todo_cli, "stats"), "todo_cli 需要新增 stats() 函数"


def test_stats_empty():
    result = todo_cli.stats()
    assert result == {"total": 0, "done": 0, "pending": 0, "done_percent": 0.0}


def test_stats_mixed():
    make_fixture()
    result = todo_cli.stats()
    assert result["total"] == 4
    assert result["done"] == 2
    assert result["pending"] == 2
    assert result["done_percent"] == 50.0


def test_stats_cli_prints():
    """通过 CLI 调用 stats 子命令要能打印结果"""
    make_fixture()
    import subprocess
    r = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(todo_cli.__file__), "todo_cli.py"), "stats"],
        capture_output=True, text=True, cwd=os.path.dirname(todo_cli.__file__),
    )
    assert r.returncode == 0, f"stats command failed: {r.stderr}"
    assert "done" in r.stdout and "percent" in r.stdout


if __name__ == "__main__":
    tests = [test_add, test_done, test_stats_function_exists,
             test_stats_empty, test_stats_mixed, test_stats_cli_prints]
    failed = 0
    for t in tests:
        setup_function()
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
        finally:
            teardown_function()
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)