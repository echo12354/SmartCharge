"""Queue query routes."""

from flask import Blueprint, request

from services.queue_service import queue_service
from utils.responses import fail, success

queue_bp = Blueprint("queue", __name__, url_prefix="/api/queues")


@queue_bp.get("/state")
def query_queue_state():
    return success("queue state", queue_service.query_queue_state())


@queue_bp.get("/me")
def query_my_queue_state():
    username = request.headers.get("X-Username") or request.args.get("userId")
    if not username:
        return fail("user id is required", 400)
    return success("car state", queue_service.query_car_state(username))

