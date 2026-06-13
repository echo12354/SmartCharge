"""一键运行作业验收用例（无需人工逐条输入）。

用法（在 backend 目录）：
    python scripts/run_acceptance_test.py
    python scripts/run_acceptance_test.py --stop 09:30
    python scripts/run_acceptance_test.py --event 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.acceptance_test_service import acceptance_test_service


def print_snapshot(snapshot: dict):
    print(f"模拟时刻: {snapshot['simTime']}")
    for label in ["快充1", "快充2", "慢充1", "慢充2", "慢充3"]:
        print(f"  {label}: {snapshot['piles'][label]}")
    print(f"  等候区: {snapshot['waitingArea']}")


def main():
    parser = argparse.ArgumentParser(description="Run SmartCharge acceptance test cases")
    parser.add_argument("--stop", default="09:30", help="Stop at simulated clock, default 09:30")
    parser.add_argument("--event", type=int, help="Run only one event index (1-42)")
    parser.add_argument("--json", action="store_true", help="Print raw JSON result")
    args = parser.parse_args()

    if args.event:
        acceptance_test_service.reset()
        result = acceptance_test_service.run_event(args.event)
        payload = result
    else:
        payload = acceptance_test_service.run_all(stop_at=args.stop)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.event:
        print(f"事件 {result['index']} @ {result['simTime']}: {result['event']}")
        print(f"动作: {result['action']}")
        print_snapshot(result["snapshot"])
        return

    print(f"共执行 {payload['executed']} 条事件，截止模拟时刻 {payload['stopAt']}")
    print("-" * 72)
    for item in payload["results"]:
        print(f"[{item['index']:02d}] {item['simTime']} {item['event']}")
        print(f"     等候区: {item['snapshot']['waitingArea']}")
        piles = item["snapshot"]["piles"]
        for label in ["快充1", "快充2", "慢充1", "慢充2", "慢充3"]:
            if piles[label] != "-":
                print(f"     {label}: {piles[label]}")
    print("-" * 72)
    print("最终状态:")
    print_snapshot(payload["finalSnapshot"])


if __name__ == "__main__":
    main()
