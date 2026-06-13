"""Fault recovery routes."""

from flask import Blueprint, request

from services.fault_recovery_service import fault_recovery_service
from utils.auth_helpers import admin_required
from utils.responses import fail, success

fault_bp = Blueprint("fault", __name__, url_prefix="/api/faults")


@fault_bp.post("/<pile_id>")
@admin_required
def create_fault(pile_id):
    data = request.get_json() or {}
    try:
        record, dispatched = fault_recovery_service.power_off_with_fault(
            pile_id,
            data.get("reason", "fault"),
            data.get("strategy", "priority"),
        )
        return success("fault handled", {
            "faultRecord": record.to_dict(),
            "dispatchedCars": [car.to_dict() for car in dispatched],
        })
    except ValueError as exc:
        return fail(str(exc), 400)


@fault_bp.post("/<pile_id>/recover")
@admin_required
def recover_fault(pile_id):
    """管理员恢复故障桩，服务层会重新启用充电桩并尝试调度同类型车辆。"""
    try:
        record, dispatched = fault_recovery_service.recover_pile(pile_id)
        return success("fault recovered", {
            "faultRecord": record.to_dict() if record else None,
            "dispatchedCars": [car.to_dict() for car in dispatched],
        })
    except ValueError as exc:
        return fail(str(exc), 400)


@fault_bp.post("/<pile_id>/priority-dispatch")
@admin_required
def priority_dispatch(pile_id):
    dispatched = fault_recovery_service.priority_dispatch(pile_id)
    return success("priority dispatch completed", {"dispatchedCars": [car.to_dict() for car in dispatched]})


@fault_bp.post("/<pile_id>/time-sequence-dispatch")
@admin_required
def time_sequence_dispatch(pile_id):
    dispatched = fault_recovery_service.time_sequence_dispatch(pile_id)
    return success("time sequence dispatch completed", {"dispatchedCars": [car.to_dict() for car in dispatched]})


@fault_bp.get("")
@admin_required
def list_faults():
    return success("fault records", {"faults": [item.to_dict() for item in fault_recovery_service.list_records()]})
