"""test_calculator.py — 计算器测试套件"""
import sys
import os

# 父目录（tests/ 的上一级）包含 buggy.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from buggy import Calculator


def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5


def test_subtract():
    calc = Calculator()
    assert calc.subtract(10, 4) == 6


def test_multiply():
    calc = Calculator()
    assert calc.multiply(3, 7) == 21


def test_divide():
    calc = Calculator()
    assert calc.divide(10, 2) == 5


def test_divide_by_zero():
    calc = Calculator()
    # 除数为 0 时应抛出 ZeroDivisionError
    try:
        calc.divide(1, 0)
        raised = False
    except ZeroDivisionError:
        raised = True
    assert raised, "divide by zero should raise ZeroDivisionError"


def test_history():
    calc = Calculator()
    calc.add(1, 2)
    calc.multiply(3, 4)
    assert len(calc.get_history()) == 2


def test_add_negative():
    calc = Calculator()
    assert calc.add(-5, 5) == 0


if __name__ == "__main__":
    tests = [
        test_add,
        test_subtract,
        test_multiply,
        test_divide,
        test_divide_by_zero,
        test_history,
        test_add_negative,
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