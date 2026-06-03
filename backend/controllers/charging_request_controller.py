"""Charging request and car state routes."""

from flask import Blueprint, request

from config.settings import MAX_ACTIVE_REQUESTS_PER_USER
from services.queue_service import queue_service
from utils.responses import fail, success

charging_request_bp = Blueprint("charging_request", __name__, url_prefix="/api/charging-requests")


def _username():
    data = request.get_json(silent=True) or {}
    return request.headers.get("X-Username") or data.get("userId") or request.args.get("userId")


def _request_id(data=None):
    payload = data if data is not None else (request.get_json(silent=True) or {})
    return payload.get("requestId") or request.args.get("requestId")


@charging_request_bp.get("")
def list_requests():
    username = _username()
    if not username:
        return fail("user id is required", 400)
    requests = [item.to_dict() for item in queue_service.list_active_requests(username)]
    return success("active requests", {
        "requests": requests,
        "total": len(requests),
        "maxAllowed": MAX_ACTIVE_REQUESTS_PER_USER,
    })


@charging_request_bp.post("")
def create_request():
    data = request.get_json() or {}
    username = _username()
    try:
        charging_request = queue_service.submit_request(
            username,
            data.get("chargeMode") or data.get("chargeType"),
            data.get("amount") or data.get("targetAmount"),
            data.get("vehicleLabel") or data.get("vehicleName") or "",
        )
        return success("charging request submitted", charging_request.to_dict(), 201)
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@charging_request_bp.patch("/amount")
def modify_amount():
    """用户仍在等候区时修改请求电量，业务上保留原排队号。"""
    data = request.get_json() or {}
    username = _username()
    try:
        charging_request = queue_service.modify_amount(
            username,
            data.get("amount") or data.get("newAmount"),
            _request_id(data),
        )
        return success("amount modified", charging_request.to_dict())
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@charging_request_bp.patch("/mode")
def modify_mode():
    """用户修改快充/慢充模式，对应切换队列并重新生成排队号。"""
    data = request.get_json() or {}
    username = _username()
    try:
        charging_request = queue_service.modify_mode(
            username,
            data.get("chargeMode") or data.get("newChargeType"),
            _request_id(data),
        )
        return success("mode modified", charging_request.to_dict())
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@charging_request_bp.get("/car-state")
def query_car_state():
    username = _username()
    if not username:
        return fail("user id is required", 400)
    return success("car state", queue_service.query_car_state(username))


@charging_request_bp.get("/<request_id>/state")
def query_request_state(request_id):
    username = _username()
    if not username:
        return fail("user id is required", 400)
    try:
        return success("request state", queue_service.query_request_state(username, request_id))
    except ValueError as exc:
        return fail(str(exc), 404)


@charging_request_bp.post("/cancel")
def cancel_request():
    """用户取消指定充电请求，服务层负责从等候区或桩队列移除车辆。"""
    data = request.get_json() or {}
    username = _username()
    try:
        charging_request = queue_service.cancel_request(username, _request_id(data))
        return success("request cancelled", charging_request.to_dict())
    except ValueError as exc:
        return fail(str(exc), 400)
