"""运行作业验收用例。

推荐本地直跑（无需启动 Flask）：
    python scripts/run_acceptance_test.py --stop 10:50 -o acceptance_result.json

通过 HTTP 接口（需先 python app.py）：
    python scripts/run_acceptance_test.py --api --stop 10:50 -o acceptance_result.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

DEFAULT_BASE_URL = "http://localhost:5001"
PILE_LABELS = ["快充1", "快充2", "慢充1", "慢充2", "慢充3"]


def api_request(base_url: str, path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"接口请求失败 {method} {path}: HTTP {exc.code}\n{body}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise SystemExit(
            f"无法连接后端服务：{base_url}\n"
            f"原因：{reason}\n"
            "请先另开终端执行：python app.py\n"
            "或改用本地模式（无需后端）：python scripts/run_acceptance_test.py --stop 10:50 -o acceptance_result.json"
        ) from exc

    result = json.loads(body)
    if not result.get("success", True):
        raise SystemExit(f"接口返回失败 {method} {path}: {result.get('message')}")
    return result.get("data", result)


def run_acceptance_local(stop_at: str = "09:30", strategy: str = "priority") -> dict:
    from services.acceptance_test_service import acceptance_test_service

    payload = acceptance_test_service.run_all(stop_at=stop_at, strategy=strategy)
    return {
        "executed": payload["executed"],
        "stopAt": payload["stopAt"],
        "results": [
            {
                "index": item["index"],
                "simTime": item["simTime"],
                "event": item["event"],
                "action": item.get("action"),
                "snapshot": item["snapshot"],
            }
            for item in payload["results"]
        ],
        "finalSnapshot": payload["finalSnapshot"],
    }


def run_single_event_local(event_index: int, strategy: str = "priority") -> dict:
    from services.acceptance_test_service import acceptance_test_service

    acceptance_test_service.reset()
    item = acceptance_test_service.run_event(event_index, strategy=strategy)
    return {
        "index": item["index"],
        "simTime": item["simTime"],
        "event": item["event"],
        "action": item.get("action"),
        "snapshot": item["snapshot"],
    }


def run_acceptance_api(base_url: str, stop_at: str = "09:30", strategy: str = "priority") -> dict:
    payload = api_request(
        base_url,
        "/api/acceptance/run-all",
        method="POST",
        payload={"stopAt": stop_at, "strategy": strategy},
    )
    return {
        "executed": payload["executed"],
        "stopAt": payload["stopAt"],
        "results": [
            {
                "index": item["index"],
                "simTime": item["simTime"],
                "event": item["event"],
                "action": item.get("action"),
                "snapshot": item["snapshot"],
            }
            for item in payload["results"]
        ],
        "finalSnapshot": payload["finalSnapshot"],
    }


def run_single_event_api(base_url: str, event_index: int, strategy: str = "priority") -> dict:
    api_request(base_url, "/api/acceptance/reset", method="POST", payload={})
    item = api_request(
        base_url,
        f"/api/acceptance/events/{event_index}",
        method="POST",
        payload={"strategy": strategy},
    )
    return {
        "index": item["index"],
        "simTime": item["simTime"],
        "event": item["event"],
        "action": item.get("action"),
        "snapshot": item["snapshot"],
    }


def print_snapshot(snapshot: dict):
    print(f"模拟时刻: {snapshot['simTime']}")
    for label in PILE_LABELS:
        print(f"  {label}: {snapshot['piles'][label]}")
    print(f"  等候区: {snapshot['waitingArea']}")


def main():
    parser = argparse.ArgumentParser(description="Run SmartCharge acceptance test cases")
    parser.add_argument("--api", action="store_true", help="通过 HTTP 调用后端（需先启动 app.py）")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL, default http://localhost:5001")
    parser.add_argument("--stop", default="09:30", help="Stop at simulated clock, default 09:30")
    parser.add_argument("--strategy", default="priority", help="Fault strategy: priority or time-sequence")
    parser.add_argument("--event", type=int, help="Run only one event index (1-42)")
    parser.add_argument("-o", "--output", help="Write JSON result to file")
    parser.add_argument("--json", action="store_true", help="Print raw JSON result")
    args = parser.parse_args()

    if args.api:
        payload = (
            run_single_event_api(args.base_url, args.event, args.strategy)
            if args.event
            else run_acceptance_api(args.base_url, stop_at=args.stop, strategy=args.strategy)
        )
    else:
        payload = (
            run_single_event_local(args.event, args.strategy)
            if args.event
            else run_acceptance_local(stop_at=args.stop, strategy=args.strategy)
        )

    if args.output:
        output_path = args.output
        if not os.path.isabs(output_path):
            output_path = os.path.join(BACKEND_ROOT, output_path)
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        print(f"已写入 JSON: {output_path}")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.event:
        print(f"事件 {payload['index']} @ {payload['simTime']}: {payload['event']}")
        print(f"动作: {payload['action']}")
        print_snapshot(payload["snapshot"])
        return

    print(f"共执行 {payload['executed']} 条事件，截止模拟时刻 {payload['stopAt']}")
    print("-" * 72)
    for item in payload["results"]:
        print(f"[{item['index']:02d}] {item['simTime']} {item['event']}")
        print(f"     等候区: {item['snapshot']['waitingArea']}")
        piles = item["snapshot"]["piles"]
        for label in PILE_LABELS:
            if piles[label] != "-":
                print(f"     {label}: {piles[label]}")
    print("-" * 72)
    print("最终状态:")
    print_snapshot(payload["finalSnapshot"])


if __name__ == "__main__":
    main()
