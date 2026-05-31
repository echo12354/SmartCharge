"""JSON response helpers."""

from flask import jsonify


def success(message: str = "success", data=None, status: int = 200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def fail(message: str, status: int = 400, data=None):
    body = {"success": False, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status

