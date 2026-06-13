"""Bill routes."""

from flask import Blueprint, request

from services.billing_service import billing_service
from utils.responses import fail, success

bill_bp = Blueprint("bill", __name__, url_prefix="/api/bills")


@bill_bp.get("/<bill_id>")
def request_bill(bill_id):
    bill = billing_service.get_bill(bill_id)
    if not bill:
        return fail("bill not found", 404)
    return success("bill detail", bill.to_dict())


@bill_bp.get("")
def request_detailed_list():
    username = request.headers.get("X-Username") or request.args.get("userId")
    bills = billing_service.list_user_bills(username) if username else billing_service.list_all_bills()
    return success("bill list", {"bills": [bill.to_dict() for bill in bills], "total": len(bills)})

