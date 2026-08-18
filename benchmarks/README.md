# Coding Agent 基准测试任务集
# 用于 dsh 驱动 Qwen3.8-27B 的标准化 Agent 作业
# 任务难度递增：每个任务输出到独立文件，便于对比

## Task 1: bug-fix — 修复 bug（简单）
任务描述:
> 在 benchmarks/workspace/tasks/task1_bug_fix/ 中有一个 buggy.py，它实现了计算器
> 但存在 3 个 bug（一个语法错误、一个逻辑错误、一个边界条件）。请修复它，
> 并运行 python3 tests/test_calculator.py 验证全部测试通过。

## Task 2: refactor — 重构（中等）
任务描述:
> 在 benchmarks/workspace/tasks/task2_refactor/ 中有 legacy.py，它是一段意大利面代码。
> 请重构为清晰的模块化结构（拆分函数、加类型注解），保持行为不变，
> 并运行 python3 tests/test_legacy.py 验证测试全部通过。

## Task 3: feature — 新功能开发（较难）
任务描述:
> 在 benchmarks/workspace/tasks/task3_feature/ 中有一个 todo_cli.py 命令行工具。
> 请新增功能：支持子命令 `stats`，统计 todo 列表中已完成/未完成的数量和百分比。
> 遵循现有代码风格，并运行 python3 tests/test_todo.py 验证全部通过。

## Task 4: multi-file — 跨文件改动（困难）
任务描述:
> 在 benchmarks/workspace/tasks/task4_multi/ 中有一个小型 Web 项目（server.py + db.py + api.py）。
> 新增一个 `GET /health` 接口，返回 {"status": "ok", "version": "1.0"}。
> 保持现有代码风格和错误处理方式，运行 python3 -m pytest 验证全部测试通过。
