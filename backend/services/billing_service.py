"""Billing service."""

from models.bill import Bill


class BillingService:
    def __init__(self):
        self.bills_by_id: dict[str, Bill] = {}
        self.bill_by_session: dict[str, Bill] = {}

    def create_bill(self, session):
        if not session.start_time or not session.end_time:
            raise ValueError("session must have start and end time")
        bill = Bill(
            session_id=session.session_id,
            user_id=session.user_id,
            pile_id=session.pile_id,
            energy_amount=session.current_amount,
            start_time=session.start_time,
            end_time=session.end_time,
            status=session.status,
        )
        self.bills_by_id[bill.bill_id] = bill
        self.bill_by_session[session.session_id] = bill
        return bill

    def get_bill(self, bill_id_or_session_id: str):
        return self.bills_by_id.get(bill_id_or_session_id) or self.bill_by_session.get(bill_id_or_session_id)

    def list_user_bills(self, user_id: str):
        bills = [bill for bill in self.bills_by_id.values() if bill.user_id == user_id]
        return sorted(bills, key=lambda bill: bill.created_at, reverse=True)

    def list_all_bills(self):
        return sorted(self.bills_by_id.values(), key=lambda bill: bill.created_at, reverse=True)


billing_service = BillingService()

