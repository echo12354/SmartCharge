"""通过后端验收接口运行作业验收用例。

用法（先启动后端服务，再在 backend 目录执行）：
    python scripts/run_acceptance_test.py
    python scripts/run_acceptance_test.py --stop 09:30
    python scripts/run_acceptance_test.py --event 2
    python scripts/run_acceptance_test.py --stop 10:50 -o acceptance_result.json
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request

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
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"接口请求失败 {method} {path}: HTTP {exc.code}\n{body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"无法连接后端服务：{base_url}\n请先启动 Flask 后端。") from exc

    result = json.loads(body)
    if not result.get("success", True):
        raise SystemExit(f"接口返回失败 {method} {path}: {result.get('message')}")
    return result.get("data", result)


def list_events(base_url: str) -> list[dict]:
    return api_request(base_url, "/api/acceptance/events")["events"]


def get_snapshot(base_url: str, strategy: str) -> dict:
    query = urllib.parse.urlencode({"strategy": strategy})
    return api_request(base_url, f"/api/acceptance/snapshot?{query}")


def run_event(base_url: str, event_index: int, strategy: str) -> dict:
    return api_request(
        base_url,
        f"/api/acceptance/events/{event_index}",
        method="POST",
        payload={"strategy": strategy},
    )


def clock_to_minutes(clock: str) -> int:
    hour, minute = [int(part) for part in clock.split(":")]
    return hour * 60 + minute


def build_result_item(event_meta: dict, event_result: dict, snapshot: dict) -> dict:
    return {
        "index": event_meta["index"],
        "simTime": event_meta["simTime"],
        "event": event_meta["event"],
        "action": event_result.get("action"),
        "snapshot": snapshot,
    }


def run_acceptance(base_url: str, stop_at: str = "09:30", strategy: str = "priority") -> dict:
    api_request(base_url, "/api/acceptance/reset", method="POST", payload={})
    events = list_events(base_url)
    stop_minutes = clock_to_minutes(stop_at)
    results = []

    for event_meta in events:
        if clock_to_minutes(event_meta["simTime"]) > stop_minutes:
            break
        event_result = run_event(base_url, event_meta["index"], strategy)
        snapshot = get_snapshot(base_url, strategy)
        results.append(build_result_item(event_meta, event_result, snapshot))

    return {
        "executed": len(results),
        "stopAt": stop_at,
        "results": results,
        "finalSnapshot": get_snapshot(base_url, strategy),
    }


def run_single_event(base_url: str, event_index: int, strategy: str = "priority") -> dict:
    api_request(base_url, "/api/acceptance/reset", method="POST", payload={})
    events = list_events(base_url)
    event_meta = next((item for item in events if item["index"] == event_index), None)
    if not event_meta:
        raise SystemExit(f"事件序号不存在: {event_index}")
    event_result = run_event(base_url, event_index, strategy)
    snapshot = get_snapshot(base_url, strategy)
    return build_result_item(event_meta, event_result, snapshot)


def print_snapshot(snapshot: dict):
    print(f"模拟时刻: {snapshot['simTime']}")
    for label in PILE_LABELS:
        print(f"  {label}: {snapshot['piles'][label]}")
    print(f"  等候区: {snapshot['waitingArea']}")


def main():
    parser = argparse.ArgumentParser(description="Run SmartCharge acceptance test cases through backend API")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL, default http://localhost:5001")
    parser.add_argument("--stop", default="09:30", help="Stop at simulated clock, default 09:30")
    parser.add_argument("--strategy", default="priority", help="Fault strategy: priority or time-sequence")
    parser.add_argument("--event", type=int, help="Run only one event index (1-42)")
    parser.add_argument("-o", "--output", help="Write JSON result to file")
    parser.add_argument("--json", action="store_true", help="Print raw JSON result")
    args = parser.parse_args()

    payload = (
        run_single_event(args.base_url, args.event, args.strategy)
        if args.event
        else run_acceptance(args.base_url, stop_at=args.stop, strategy=args.strategy)
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        print(f"已写入 JSON: {args.output}")

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
