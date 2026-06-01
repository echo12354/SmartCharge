"""Charging request and car state routes."""

from flask import Blueprint, request

from services.queue_service import queue_service
from utils.responses import fail, success

charging_request_bp = Blueprint("charging_request", __name__, url_prefix="/api/charging-requests")


@charging_request_bp.post("")
def create_request():
    data = request.get_json() or {}
    username = request.headers.get("X-Username") or data.get("userId")
    try:
        charging_request = queue_service.submit_request(
            username,
            data.get("chargeMode") or data.get("chargeType"),
            data.get("amount") or data.get("targetAmount"),
        )
        return success("charging request submitted", charging_request.to_dict(), 201)
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@charging_request_bp.patch("/amount")
def modify_amount():
    """用户仍在等候区时修改请求电量，业务上保留原排队号。"""
    data = request.get_json() or {}
    username = request.headers.get("X-Username") or data.get("userId")
    try:
        charging_request = queue_service.modify_amount(username, data.get("amount") or data.get("newAmount"))
        return success("amount modified", charging_request.to_dict())
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@charging_request_bp.patch("/mode")
def modify_mode():
    """用户修改快充/慢充模式，对应切换队列并重新生成排队号。"""
    data = request.get_json() or {}
    username = request.headers.get("X-Username") or data.get("userId")
    try:
        charging_request = queue_service.modify_mode(username, data.get("chargeMode") or data.get("newChargeType"))
        return success("mode modified", charging_request.to_dict())
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@charging_request_bp.get("/car-state")
def query_car_state():
    username = request.headers.get("X-Username") or request.args.get("userId")
    if not username:
        return fail("user id is required", 400)
    return success("car state", queue_service.query_car_state(username))


@charging_request_bp.post("/cancel")
def cancel_request():
    """用户取消当前充电请求，服务层负责从等候区或桩队列移除车辆。"""
    data = request.get_json() or {}
    username = request.headers.get("X-Username") or data.get("userId")
    try:
        charging_request = queue_service.cancel_request(username)
        return success("request cancelled", charging_request.to_dict())
    except ValueError as exc:
        return fail(str(exc), 400)

