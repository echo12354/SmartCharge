"""将 acceptance_result.json 的测试结果写入《作业验收用例.xlsx》。

用法（在 backend 目录）：
    pip install openpyxl
    python scripts/run_acceptance_test.py --stop 10:50 -o acceptance_result.json
    python scripts/fill_acceptance_xlsx.py
    python scripts/fill_acceptance_xlsx.py -i acceptance_result.json -t ../作业验收用例.xlsx -o ../作业验收用例_已填写.xlsx
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)

PILE_LABELS = ["快充1", "快充2", "慢充1", "慢充2", "慢充3"]
# 测试用例 sheet：第 1 条事件从第 3 行开始，每条事件占 3 行。
FIRST_EVENT_ROW = 3
ROWS_PER_EVENT = 3
COL_TIME = 1
COL_EVENT = 2
COL_PILE_START = 3
COL_WAITING = 8


def clock_to_excel_fraction(clock: str) -> float:
    hour, minute = [int(part) for part in clock.split(":")]
    return round((hour * 60 + minute) / (24 * 60), 12)


def split_cell_entries(value: str | None) -> list[str]:
    """将 `(a)-(b)-(c)` 拆成最多 3 行，纵向写入同一列。"""
    if not value or value == "-":
        return ["-"] * ROWS_PER_EVENT
    parts = re.findall(r"\([^)]+\)", value)
    if not parts:
        return ["-"] * ROWS_PER_EVENT
    while len(parts) < ROWS_PER_EVENT:
        parts.append("-")
    return parts[:ROWS_PER_EVENT]


def unmerge_pile_columns(sheet, base_row: int):
    """解除当前事件 3 行范围内充电桩列的合并单元格（等候区不在此处理）。"""
    target_cols = list(range(COL_PILE_START, COL_PILE_START + len(PILE_LABELS)))
    merged_ranges = list(sheet.merged_cells.ranges)
    for merged_range in merged_ranges:
        min_col, min_row, max_col, max_row = merged_range.bounds
        if max_row < base_row or min_row >= base_row + ROWS_PER_EVENT:
            continue
        if not any(min_col <= col <= max_col for col in target_cols):
            continue
        sheet.unmerge_cells(str(merged_range))


def write_pile_column_rows(sheet, column: int, base_row: int, value: str | None):
    """充电桩列：最多 3 辆车纵向分 3 行填写。"""
    unmerge_pile_columns(sheet, base_row)
    for offset, cell_value in enumerate(split_cell_entries(value)):
        row = base_row + offset
        sheet.cell(row=row, column=column, value="-" if cell_value == "-" else cell_value)


def write_waiting_area(sheet, base_row: int, value: str | None):
    """等候区：最多 10 辆车，全部写在同一格（一行），用 `-` 连接。"""
    unmerge_pile_columns(sheet, base_row)
    for row in range(base_row, base_row + ROWS_PER_EVENT):
        sheet.cell(row=row, column=COL_WAITING, value=None)
    if value and value != "-":
        sheet.cell(row=base_row, column=COL_WAITING, value=value)


def load_results(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as file:
        payload = json.load(file)
    if "results" in payload:
        return payload["results"]
    return [payload]


def fill_workbook(results: list[dict], template_path: str, output_path: str):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise SystemExit("请先安装 openpyxl：pip install openpyxl") from exc

    workbook = load_workbook(template_path)
    if "测试用例" in workbook.sheetnames:
        sheet = workbook["测试用例"]
    else:
        sheet = workbook.worksheets[1]

    for index, item in enumerate(results):
        base_row = FIRST_EVENT_ROW + index * ROWS_PER_EVENT
        snapshot = item["snapshot"]
        piles = snapshot["piles"]

        sheet.cell(row=base_row, column=COL_TIME, value=clock_to_excel_fraction(item["simTime"]))
        sheet.cell(row=base_row, column=COL_EVENT, value=item["event"])
        for extra_row in range(base_row + 1, base_row + ROWS_PER_EVENT):
            sheet.cell(row=extra_row, column=COL_TIME, value=None)
            sheet.cell(row=extra_row, column=COL_EVENT, value=None)

        for offset, label in enumerate(PILE_LABELS):
            write_pile_column_rows(sheet, COL_PILE_START + offset, base_row, piles.get(label, "-"))

        waiting = snapshot.get("waitingArea", "-") or "-"
        write_waiting_area(sheet, base_row, waiting)

    workbook.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="Fill acceptance test JSON into Excel template")
    parser.add_argument(
        "-i", "--input",
        default=os.path.join(BACKEND_ROOT, "acceptance_result.json"),
        help="acceptance_result.json path",
    )
    parser.add_argument(
        "-t", "--template",
        default=os.path.join(PROJECT_ROOT, "作业验收用例.xlsx"),
        help="Excel template path",
    )
    parser.add_argument(
        "-o", "--output",
        default=os.path.join(PROJECT_ROOT, "作业验收用例_已填写.xlsx"),
        help="Output Excel path (default: do not overwrite template)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        raise SystemExit(f"找不到 JSON 文件: {args.input}\n请先运行: python scripts/run_acceptance_test.py --stop 10:50 -o acceptance_result.json")
    if not os.path.isfile(args.template):
        raise SystemExit(f"找不到 Excel 模板: {args.template}")

    results = load_results(args.input)
    fill_workbook(results, args.template, args.output)
    print(f"已写入 {len(results)} 条事件")
    print(f"输出文件: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
