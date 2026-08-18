"""buggy.py — 计算器实现，故意包含 3 个 bug

Bug 1: 语法错误（第 29 行附近，缺冒号）
Bug 2: 逻辑错误（divide 除数为 0 时返回错误结果）
Bug 3: 边界条件（add 对字符串类型处理不当）
"""


class Calculator:
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self._record(f"{a} + {b} = {result}")
        return result

    def subtract(self, a, b):
        result = a - b
        self._record(f"{a} - {b} = {result}")
        return result

    def multiply(self, a, b):
        result = a * b
        self._record(f"{a} * {b} = {result}")
        return result

    def divide(self, a, b)
        if b == 0:
            result = 0
        else:
            result = a / b
        self._record(f"{a} / {b} = {result}")
        return result

    def _record(self, entry):
        self.history.append(entry)

    def get_history(self):
        return list(self.history)