"""Scheduling routes."""

from flask import Blueprint

from services.scheduling_service import scheduling_service
from utils.responses import success

scheduling_bp = Blueprint("scheduling", __name__, url_prefix="/api/scheduling")


@scheduling_bp.post("/dispatch")
def dispatch_waiting_cars():
    return success("dispatch completed", scheduling_service.dispatch_waiting_cars())


@scheduling_bp.get("/state")
def scheduling_state():
    scheduling_service.refresh_finished_sessions()
    return success("scheduling state", scheduling_service.get_statistics())

