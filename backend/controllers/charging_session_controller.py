"""充电会话接口。

处理开始充电、查询充电状态、结束充电和活跃会话列表。
"""

from flask import Blueprint, request

from services.charging_session_service import charging_session_service
from services.scheduling_service import scheduling_service
from utils.responses import fail, success

charging_session_bp = Blueprint("charging_session", __name__, url_prefix="/api/charging-sessions")


@charging_session_bp.post("/start")
def start_charging():
    data = request.get_json() or {}
    try:
        session = scheduling_service.start_charging(data.get("pileId"), data.get("userId"))
        return success("charging started", session.to_dict(), 201)
    except ValueError as exc:
        return fail(str(exc), 400)


@charging_session_bp.get("/state")
def query_charging_state():
    username = request.headers.get("X-Username") or request.args.get("userId")
    session_id = request.args.get("sessionId")
    session = charging_session_service.get_session(session_id) if session_id else charging_session_service.get_user_active_session(username)
    if not session:
        return success("no active charging session", {"hasActiveCharging": False})
    return success("charging state", {"hasActiveCharging": session.status == "CHARGING", "session": session.to_dict()})


@charging_session_bp.post("/<session_id>/end")
def end_charging(session_id):
    """用户或管理员结束充电时，服务层会同步生成账单。"""
    data = request.get_json() or {}
    try:
        session, bill = scheduling_service.end_charging(session_id, data.get("reason", "manual stop"))
        return success("charging ended", {"session": session.to_dict(), "bill": bill.to_dict()})
    except ValueError as exc:
        return fail(str(exc), 400)


@charging_session_bp.get("")
def list_active_sessions():
    return success("active sessions", {"sessions": [item.to_dict() for item in charging_session_service.list_active_sessions()]})

