"""统一 JSON 响应工具。

Controller 通过这里保持成功和失败响应结构一致。
"""

from flask import jsonify


def success(message: str = "success", data=None, status: int = 200):
    """成功响应：固定包含 success 和 message，按需携带 data。"""
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def fail(message: str, status: int = 400, data=None):
    """失败响应：固定包含 success=False 和错误信息。"""
    body = {"success": False, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status

