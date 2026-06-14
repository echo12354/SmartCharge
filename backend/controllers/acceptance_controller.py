"""验收测试自动化接口。"""

from flask import Blueprint, request

from services.acceptance_test_service import acceptance_test_service
from utils.responses import fail, success

acceptance_bp = Blueprint("acceptance", __name__, url_prefix="/api/acceptance")


@acceptance_bp.post("/reset")
def reset_acceptance():
    return success("acceptance reset", acceptance_test_service.reset())


@acceptance_bp.post("/run-all")
def run_all_acceptance():
    data = request.get_json(silent=True) or {}
    stop_at = data.get("stopAt", request.args.get("stopAt", "09:30"))
    strategy = data.get("strategy", request.args.get("strategy", "priority"))
    try:
        return success("acceptance run completed", acceptance_test_service.run_all(stop_at=stop_at, strategy=strategy))
    except Exception as exc:
        return fail(str(exc), 500)


@acceptance_bp.post("/events/<int:event_index>")
def run_acceptance_event(event_index: int):
    data = request.get_json(silent=True) or {}
    strategy = data.get("strategy", request.args.get("strategy", "priority"))
    try:
        return success("acceptance event executed", acceptance_test_service.run_event(event_index, strategy=strategy))
    except ValueError as exc:
        return fail(str(exc), 400)


@acceptance_bp.post("/events/next")
def run_next_acceptance_event():
    data = request.get_json(silent=True) or {}
    strategy = data.get("strategy", request.args.get("strategy", "priority"))
    try:
        return success("acceptance event executed", acceptance_test_service.run_next(strategy=strategy))
    except ValueError as exc:
        return fail(str(exc), 400)


@acceptance_bp.get("/snapshot")
def acceptance_snapshot():
    strategy = request.args.get("strategy", "priority")
    try:
        return success("acceptance snapshot", acceptance_test_service.get_snapshot(strategy=strategy))
    except Exception as exc:
        return fail(str(exc), 500)


@acceptance_bp.get("/events")
def list_acceptance_events():
    from services.acceptance_test_service import ACCEPTANCE_EVENTS
    return success("acceptance events", {
        "events": [
            {"index": index, "simTime": clock, "event": acceptance_test_service._format_event(event)}
            for index, (clock, event) in enumerate(ACCEPTANCE_EVENTS, start=1)
        ],
        "total": len(ACCEPTANCE_EVENTS),
    })
