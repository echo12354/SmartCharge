"""Compatibility routes matching the original backend API shape.

These routes keep the redesigned code usable with flows from the original
project while still delegating to the new service names and model structure.
"""

from flask import Blueprint, request

from services.billing_service import billing_service
from services.charging_session_service import charging_session_service
from services.fault_recovery_service import fault_recovery_service
from services.pile_management_service import pile_management_service
from services.queue_service import WaitingAreaFullError, queue_service
from services.scheduling_service import scheduling_service
from services.user_service import user_service
from utils.responses import fail, success

compat_bp = Blueprint("compat", __name__, url_prefix="/api")


def _username():
    data = request.get_json(silent=True) or {}
    return request.headers.get("X-Username") or request.args.get("userId") or data.get("userId") or data.get("username")


@compat_bp.post("/register")
def legacy_register():
    data = request.get_json() or {}
    try:
        user = user_service.register(data.get("username"), data.get("password"), data.get("type", "user"))
        return success("注册成功", {"username": user.username})
    except ValueError as exc:
        return fail(str(exc), 400)


@compat_bp.post("/login")
def legacy_login():
    data = request.get_json() or {}
    try:
        user = user_service.login(data.get("username"), data.get("password"))
        return {"type": user.role}
    except ValueError as exc:
        return fail(str(exc), 401)


@compat_bp.get("/user/info")
def legacy_user_info():
    user = user_service.get_user(_username())
    if not user:
        return fail("用户不存在", 404)
    return success("获取用户信息成功", user.to_dict())


@compat_bp.get("/user/statistics")
def legacy_user_statistics():
    username = _username()
    bills = billing_service.list_user_bills(username)
    return success("获取用户统计成功", {
        "chargeCount": len(bills),
        "totalEnergy": round(sum(bill.energy_amount for bill in bills), 2),
        "totalCost": round(sum(bill.total_fee for bill in bills), 2),
    })


@compat_bp.get("/users")
def legacy_users():
    return success("获取用户列表成功", {
        "users": [user.to_dict() for user in user_service.users.values()],
        "total": len(user_service.users),
    })


@compat_bp.post("/charging/request")
def legacy_charging_request():
    data = request.get_json() or {}
    username = _username()
    try:
        created = queue_service.submit_request(
            username,
            data.get("chargeType") or data.get("chargeMode"),
            data.get("targetAmount") or data.get("amount"),
            data.get("vehicleLabel") or data.get("vehicleName") or "",
            data.get("batteryCapacity") or data.get("battery_capacity") or 0,
        )
        return success("充电请求提交成功", created.to_dict())
    except WaitingAreaFullError as exc:
        return fail(str(exc), 409)
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@compat_bp.get("/charging/current")
def legacy_current_charging():
    state = queue_service.query_car_state(_username())
    session = state.get("chargingSession")
    if session:
        return success("获取充电状态成功", {
            "hasActiveCharging": True,
            "status": "charging",
            "session": session,
            "queue": state.get("pileQueue"),
        })
    if state.get("state") != "IDLE":
        return success("获取充电状态成功", {
            "hasActiveCharging": False,
            "status": "waiting",
            "queue": state,
        })
    return success("获取充电状态成功", {"hasActiveCharging": False, "status": "idle"})


@compat_bp.get("/queue/status")
def legacy_queue_status():
    return success("获取排队状态成功", queue_service.query_car_state(_username()))


@compat_bp.post("/queue/cancel")
def legacy_cancel_queue():
    try:
        cancelled = queue_service.cancel_request(_username())
        return success("充电请求已取消", cancelled.to_dict())
    except ValueError as exc:
        return fail(str(exc), 400)


@compat_bp.post("/queue/modify-amount")
def legacy_modify_amount():
    data = request.get_json() or {}
    try:
        modified = queue_service.modify_amount(_username(), data.get("newAmount") or data.get("amount"))
        return success("充电量修改成功", modified.to_dict())
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@compat_bp.post("/queue/modify-mode")
def legacy_modify_mode():
    data = request.get_json() or {}
    try:
        modified = queue_service.modify_mode(_username(), data.get("newChargeType") or data.get("chargeMode"))
        return success("充电模式修改成功", modified.to_dict())
    except (ValueError, TypeError) as exc:
        return fail(str(exc), 400)


@compat_bp.get("/queue/charge-area")
def legacy_charge_area():
    return success("获取充电区状态成功", queue_service.query_charge_area_state())


@compat_bp.get("/queue/ahead-count")
def legacy_ahead_count():
    return success("获取前车等待数量成功", {"aheadCount": queue_service.get_queue_ahead_count(_username())})


@compat_bp.get("/admin/statistics/piles")
def legacy_admin_pile_statistics():
    stats = pile_management_service.get_statistics()
    stats["totalQueuedCars"] = len(queue_service.waiting_queue.cars)
    stats["totalRevenue"] = round(sum(bill.total_fee for bill in billing_service.list_all_bills()), 2)
    return success("获取统计数据成功", stats)


@compat_bp.get("/admin/piles")
def legacy_admin_piles():
    piles = []
    for index, pile in enumerate(pile_management_service.list_piles(), start=1):
        data = pile.to_dict()
        data["id"] = index
        data["name"] = pile.pile_id
        data["isActive"] = pile.is_enabled
        data["queueCount"] = len(scheduling_service.pile_queues[pile.pile_id].cars())
        piles.append(data)
    return success("获取充电桩列表成功", {"piles": piles})


@compat_bp.post("/admin/piles/<int:pile_id>/status")
def legacy_update_pile_status(pile_id):
    pile_char = chr(ord("A") + pile_id - 1)
    data = request.get_json() or {}
    try:
        if data.get("isActive"):
            record, dispatched = fault_recovery_service.recover_pile(pile_char)
            return success("充电桩启动成功", {
                "pileId": pile_id,
                "isActive": True,
                "faultRecord": record.to_dict() if record else None,
                "rescheduledCars": [car.user_id for car in dispatched],
            })
        record, dispatched = fault_recovery_service.power_off_with_fault(pile_char, "管理员手动关闭")
        return success("充电桩关闭成功", {
            "pileId": pile_id,
            "isActive": False,
            "affectedCars": record.affected_car_ids,
            "rescheduledCars": [car.user_id for car in dispatched],
        })
    except ValueError as exc:
        return fail(str(exc), 400)


@compat_bp.get("/admin/queue")
def legacy_admin_queue():
    return success("获取队列信息成功", {"cars": queue_service.get_admin_queue_info()})


@compat_bp.get("/admin/reports")
def legacy_admin_reports():
    return success("获取报表数据成功", {"reports": pile_management_service.get_reports()})


@compat_bp.get("/admin/piles/<int:pile_id>/details")
def legacy_pile_details(pile_id):
    pile_char = chr(ord("A") + pile_id - 1)
    pile = pile_management_service.get_pile(pile_char)
    if not pile:
        return fail("充电桩不存在", 404)
    queue_info = queue_service.get_queue_for_pile(pile_char)
    return success("获取充电桩详情成功", {
        "pileId": pile_id,
        "name": pile_char,
        "isActive": pile.is_enabled,
        "power": pile.power,
        "type": pile.pile_type,
        "status": pile.status,
        "totalCharges": pile.total_sessions,
        "totalHours": round(pile.total_hours, 2),
        "totalEnergy": round(pile.total_energy, 2),
        "queueCount": len(scheduling_service.pile_queues[pile_char].cars()),
        "currentCharging": queue_info.get("currentCharging") if queue_info else None,
        "queueList": queue_info.get("waitingCars", []) if queue_info else [],
    })


@compat_bp.get("/dispatch/statistics")
def legacy_dispatch_statistics():
    return success("获取调度统计成功", scheduling_service.get_statistics())


@compat_bp.get("/dispatch/pile-queues")
def legacy_pile_queues():
    return success("获取充电桩队列状态成功", scheduling_service.get_all_pile_queues())


@compat_bp.get("/dispatch/pile-queue/<pile_id>")
def legacy_pile_queue(pile_id):
    queue = scheduling_service.get_pile_queue(pile_id)
    if not queue:
        return fail("充电桩队列不存在", 404)
    return success("获取充电桩队列状态成功", queue)


@compat_bp.post("/dispatch/engine/start")
def legacy_start_dispatch_engine():
    return success("调度引擎已启动", scheduling_service.start_engine())


@compat_bp.post("/dispatch/engine/stop")
def legacy_stop_dispatch_engine():
    return success("调度引擎已停止", scheduling_service.stop_engine())


@compat_bp.get("/dispatch/engine/status")
def legacy_dispatch_engine_status():
    stats = scheduling_service.get_statistics()
    return success("获取调度引擎状态成功", {
        "isRunning": stats["engineRunning"],
        "totalDispatched": stats["totalDispatched"],
        "pileUtilization": stats["pileUtilization"],
        "recentDecisions": stats["recentDecisions"],
    })


@compat_bp.get("/admin/dispatch/overview")
def legacy_dispatch_overview():
    stats = scheduling_service.get_statistics()
    return success("获取调度概览成功", {
        "engineStatus": {
            "isRunning": stats["engineRunning"],
            "totalDispatched": stats["totalDispatched"],
        },
        "pileQueues": list(stats["pileQueues"].values()),
        "utilizationSummary": stats["pileUtilization"],
        "queueCapacity": stats["queueCapacity"],
        "recentDecisions": stats["recentDecisions"],
    })


@compat_bp.get("/charging/session/status")
def legacy_session_status():
    session = charging_session_service.get_user_active_session(_username())
    if not session:
        return success("无活跃充电会话", {"hasActiveCharging": False})
    return success("获取充电会话状态成功", session.to_dict())


@compat_bp.get("/charging/session/history")
def legacy_session_history():
    username = _username()
    sessions = charging_session_service.list_user_sessions(username)
    return success("获取充电历史成功", {
        "sessions": [session.to_dict() for session in sessions],
        "totalCount": len(sessions),
    })


@compat_bp.post("/charging/session/<session_id>/stop")
def legacy_stop_session(session_id):
    data = request.get_json() or {}
    try:
        session, bill = scheduling_service.end_charging(session_id, data.get("reason", "用户主动停止"))
        return success("充电会话已停止", {"sessionId": session_id, "bill": bill.to_dict()})
    except ValueError as exc:
        return fail(str(exc), 400)


@compat_bp.get("/charging/session/<session_id>/bill")
def legacy_session_bill(session_id):
    bill = billing_service.get_bill(session_id)
    if not bill:
        return fail("充电详单未生成", 404)
    return success("获取充电详单成功", bill.to_dict())


@compat_bp.get("/charging/real-time-status")
def legacy_real_time_status():
    sessions = [session.to_dict() for session in charging_session_service.list_active_sessions()]
    return success("获取实时状态成功", {
        "activeSessions": sessions,
        "totalActiveSessions": len(sessions),
    })


@compat_bp.get("/admin/charging/sessions")
def legacy_admin_sessions():
    sessions = [session.to_dict() for session in charging_session_service.list_active_sessions()]
    return success("获取充电会话列表成功", {"sessions": sessions, "totalCount": len(sessions)})


@compat_bp.get("/admin/charging/statistics")
def legacy_admin_charging_statistics():
    return success("获取充电统计成功", charging_session_service.get_statistics())


@compat_bp.post("/admin/charging/session/<session_id>/stop")
def legacy_admin_stop_session(session_id):
    return legacy_stop_session(session_id)


@compat_bp.get("/charging/process/monitor/status")
def legacy_monitor_status():
    return success("获取监控状态成功", {
        "timestamp": None,
        "monitorRunning": True,
        "activeSessions": [session.to_dict() for session in charging_session_service.list_active_sessions()],
    })


@compat_bp.get("/charging/records")
def legacy_charging_records():
    username = _username()
    bills = billing_service.list_user_bills(username)
    return success("获取充电记录成功", {
        "records": [bill.to_dict() for bill in bills],
        "totalCount": len(bills),
        "totalEnergy": round(sum(bill.energy_amount for bill in bills), 2),
        "totalCost": round(sum(bill.total_fee for bill in bills), 2),
    })
