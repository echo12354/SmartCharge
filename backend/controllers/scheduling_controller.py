"""调度接口。

提供手动触发调度和查询当前调度状态的入口。
"""

from flask import Blueprint

from services.scheduling_service import scheduling_service
from utils.responses import success

scheduling_bp = Blueprint("scheduling", __name__, url_prefix="/api/scheduling")


@scheduling_bp.post("/dispatch")
def dispatch_waiting_cars():
    """手动触发一次等候区到充电桩队列的调度。"""
    return success("dispatch completed", scheduling_service.dispatch_waiting_cars())


@scheduling_bp.get("/state")
def scheduling_state():
    scheduling_service.refresh_finished_sessions()
    return success("scheduling state", scheduling_service.get_statistics())

