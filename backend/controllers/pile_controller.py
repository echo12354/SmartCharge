"""Charging pile routes."""

from flask import Blueprint, request

from services.fault_recovery_service import fault_recovery_service
from services.pile_management_service import pile_management_service
from services.scheduling_service import scheduling_service
from utils.auth_helpers import admin_required
from utils.responses import fail, success

pile_bp = Blueprint("pile", __name__, url_prefix="/api/piles")


@pile_bp.get("")
def list_piles():
    return success("pile list", {"piles": [pile.to_dict() for pile in pile_management_service.list_piles()]})


@pile_bp.get("/<pile_id>")
def query_pile_state(pile_id):
    pile = pile_management_service.get_pile(pile_id)
    if not pile:
        return fail("pile not found", 404)
    return success("pile state", {
        "pile": pile.to_dict(),
        "queue": scheduling_service.pile_queues[pile_id].to_dict(),
    })


@pile_bp.post("/<pile_id>/power-on")
@admin_required
def power_on(pile_id):
    try:
        record, dispatched = fault_recovery_service.recover_pile(pile_id)
        return success("pile powered on", {
            "pile": pile_management_service.get_pile(pile_id).to_dict(),
            "faultRecord": record.to_dict() if record else None,
            "dispatchedCars": [car.to_dict() for car in dispatched],
        })
    except ValueError as exc:
        return fail(str(exc), 400)


@pile_bp.post("/<pile_id>/power-off")
@admin_required
def power_off(pile_id):
    """管理员关闭充电桩时按故障场景处理，并触发受影响车辆重新调度。"""
    data = request.get_json() or {}
    try:
        record, dispatched = fault_recovery_service.power_off_with_fault(
            pile_id,
            data.get("reason", "manual power off"),
            data.get("strategy", "priority"),
        )
        return success("pile powered off", {
            "faultRecord": record.to_dict(),
            "dispatchedCars": [car.to_dict() for car in dispatched],
        })
    except ValueError as exc:
        return fail(str(exc), 400)


@pile_bp.post("/<pile_id>/start")
@admin_required
def start_pile(pile_id):
    try:
        pile = pile_management_service.start_pile(pile_id)
        return success("pile started", pile.to_dict())
    except ValueError as exc:
        return fail(str(exc), 400)


@pile_bp.patch("/<pile_id>/parameters")
@admin_required
def set_parameters(pile_id):
    try:
        pile = pile_management_service.set_parameters(pile_id, request.get_json() or {})
        return success("parameters updated", pile.to_dict())
    except ValueError as exc:
        return fail(str(exc), 400)
