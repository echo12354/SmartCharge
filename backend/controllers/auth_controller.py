"""Authentication routes."""

from flask import Blueprint, request

from services.user_service import user_service
from utils.responses import fail, success

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    try:
        user = user_service.register(data.get("username"), data.get("password"), data.get("role", "user"))
        return success("registered", user.to_dict(), 201)
    except ValueError as exc:
        return fail(str(exc), 400)


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    try:
        user = user_service.login(data.get("username"), data.get("password"))
        return success("login success", user.to_dict())
    except ValueError as exc:
        return fail(str(exc), 401)

