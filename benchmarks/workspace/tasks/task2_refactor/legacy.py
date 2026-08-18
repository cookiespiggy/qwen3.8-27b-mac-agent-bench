"""legacy.py — 意大利面代码，需要重构（Task 2）

重构目标:
1. 拆分长函数为职责单一的小函数
2. 添加类型注解
3. 保持对外行为完全一致
"""


def process(data, mode="sum", verbose=False):
    total = 0
    count = 0
    max_val = None
    min_val = None
    for x in data:
        if isinstance(x, (int, float)):
            total = total + x
            count = count + 1
            if max_val is None or x > max_val:
                max_val = x
            if min_val is None or x < min_val:
                min_val = x
    if verbose:
        print("processing done")
    if mode == "sum":
        return total
    elif mode == "avg":
        if count == 0:
            return 0
        return total / count
    elif mode == "stats":
        return {"sum": total, "count": count, "max": max_val, "min": min_val}
    else:
        raise ValueError(f"unknown mode: {mode}")


def analyze_and_filter(data, threshold, mode="sum"):
    filtered = [x for x in data if isinstance(x, (int, float)) and x >= threshold]
    result = process(filtered, mode=mode)
    filtered_total = sum(filtered) if filtered else 0
    return {"result": result, "filtered_total": filtered_total, "filtered_count": len(filtered)}


def load_numbers(path):
    nums = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    nums.append(float(line))
                except ValueError:
                    continue
    return nums


def main():
    import sys
    if len(sys.argv) < 2:
        print("usage: python3 legacy.py <datafile>")
        return
    data = load_numbers(sys.argv[1])
    print(analyze_and_filter(data, threshold=0, mode="stats"))


if __name__ == "__main__":
    main()