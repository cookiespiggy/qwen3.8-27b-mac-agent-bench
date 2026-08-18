"""test_legacy.py — legacy.py 行为测试（重构后必须全部通过）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legacy import process, analyze_and_filter


def test_process_sum():
    assert process([1, 2, 3, 4]) == 10


def test_process_avg():
    assert process([1, 2, 3, 4], mode="avg") == 2.5


def test_process_stats():
    s = process([1, 2, 3, 4], mode="stats")
    assert s == {"sum": 10, "count": 4, "max": 4, "min": 1}


def test_process_ignores_non_numbers():
    assert process([1, "a", None, 2, "b"]) == 3


def test_process_avg_empty():
    assert process([], mode="avg") == 0


def test_process_unknown_mode():
    try:
        process([1], mode="bogus")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_analyze_and_filter():
    r = analyze_and_filter([1, 2, 5, 8, 9], threshold=5, mode="sum")
    assert r["result"] == 22
    assert r["filtered_total"] == 22
    assert r["filtered_count"] == 3


def test_analyze_and_filter_none():
    r = analyze_and_filter(["a", "b"], threshold=0, mode="sum")
    assert r["result"] == 0
    assert r["filtered_total"] == 0
    assert r["filtered_count"] == 0


if __name__ == "__main__":
    tests = [
        test_process_sum,
        test_process_avg,
        test_process_stats,
        test_process_ignores_non_numbers,
        test_process_avg_empty,
        test_process_unknown_mode,
        test_analyze_and_filter,
        test_analyze_and_filter_none,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)