"""HTTP 请求身份与管理员权限校验。"""

from functools import wraps

from flask import request

from services.user_service import user_service


def get_request_username() -> str | None:
    data = request.get_json(silent=True) or {}
    return (
        request.headers.get("X-Username")
        or data.get("userId")
        or request.args.get("userId")
        or data.get("username")
    )


def enforce_admin():
    username = get_request_username()
    if not username:
        raise PermissionError("authentication required")
    return user_service.require_admin(username)


def admin_required(view):
    """装饰器：仅允许管理员角色访问。"""

    @wraps(view)
    def wrapper(*args, **kwargs):
        from utils.responses import fail

        try:
            enforce_admin()
        except PermissionError as exc:
            return fail(str(exc), 403)
        return view(*args, **kwargs)

    return wrapper
