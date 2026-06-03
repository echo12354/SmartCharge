"""Queue query routes."""

from flask import Blueprint, request

from services.queue_service import queue_service
from utils.responses import fail, success

queue_bp = Blueprint("queue", __name__, url_prefix="/api/queues")


@queue_bp.get("/state")
def query_queue_state():
    return success("queue state", queue_service.query_queue_state())


@queue_bp.get("/ahead-count")
def query_ahead_count():
    username = request.headers.get("X-Username") or request.args.get("userId")
    request_id = request.args.get("requestId")
    if not username:
        return fail("user id is required", 400)
    try:
        ahead_count = queue_service.get_queue_ahead_count(username, request_id)
        return success("ahead count", {"aheadCount": ahead_count, "requestId": request_id})
    except ValueError as exc:
        return fail(str(exc), 400)


@queue_bp.get("/me")
def query_my_queue_state():
    username = request.headers.get("X-Username") or request.args.get("userId")
    if not username:
        return fail("user id is required", 400)
    return success("car state", queue_service.query_car_state(username))
