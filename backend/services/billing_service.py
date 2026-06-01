"""Billing service."""

from models.bill import Bill
from repositories.bill_repository import BillRepository


class BillingService:
    def __init__(self):
        self.bills_by_id: dict[str, Bill] = {}
        self.bill_by_session: dict[str, Bill] = {}
        self.repository = BillRepository()

    def create_bill(self, session):
        if not session.start_time or not session.end_time:
            raise ValueError("session must have start and end time")
        existing = self.get_bill(session.session_id)
        if existing:
            return existing
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
        self._save_bill_to_database(bill)
        return bill

    def get_bill(self, bill_id_or_session_id: str):
        bill = self._get_bill_from_database(bill_id_or_session_id)
        if bill:
            self._cache_bill(bill)
            return bill
        return self.bills_by_id.get(bill_id_or_session_id) or self.bill_by_session.get(bill_id_or_session_id)

    def list_user_bills(self, user_id: str):
        bills = self._list_user_bills_from_database(user_id)
        if bills is not None:
            for bill in bills:
                self._cache_bill(bill)
            return bills
        bills = [bill for bill in self.bills_by_id.values() if bill.user_id == user_id]
        return sorted(bills, key=lambda bill: bill.created_at, reverse=True)

    def list_all_bills(self):
        bills = self._list_all_bills_from_database()
        if bills is not None:
            for bill in bills:
                self._cache_bill(bill)
            return bills
        return sorted(self.bills_by_id.values(), key=lambda bill: bill.created_at, reverse=True)

    def _cache_bill(self, bill: Bill):
        self.bills_by_id[bill.bill_id] = bill
        self.bill_by_session[bill.session_id] = bill

    def _save_bill_to_database(self, bill: Bill):
        try:
            self.repository.save_bill(bill)
        except Exception:
            pass

    def _get_bill_from_database(self, bill_id_or_session_id: str):
        try:
            return self.repository.get_bill(bill_id_or_session_id)
        except Exception:
            return None

    def _list_user_bills_from_database(self, user_id: str):
        try:
            return self.repository.list_user_bills(user_id)
        except Exception:
            return None

    def _list_all_bills_from_database(self):
        try:
            return self.repository.list_all_bills()
        except Exception:
            return None


billing_service = BillingService()

