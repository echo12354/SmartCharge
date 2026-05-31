"""Charging session service."""

from models.charging_session import ChargingSession
from services.billing_service import billing_service
from services.pile_management_service import pile_management_service


class ChargingSessionService:
    def __init__(self):
        self.active_sessions: dict[str, ChargingSession] = {}
        self.completed_sessions: dict[str, ChargingSession] = {}
        self.user_active_session: dict[str, str] = {}
        self.pile_active_session: dict[str, str] = {}

    def create_and_start(self, user_id: str, pile_id: str, amount: float, request_id: str | None = None):
        if user_id in self.user_active_session:
            return self.active_sessions[self.user_active_session[user_id]]
        if pile_id in self.pile_active_session:
            raise ValueError("pile already has active session")
        pile = pile_management_service.get_pile(pile_id)
        if not pile or not pile.is_enabled:
            raise ValueError("pile is not available")
        session = ChargingSession(
            user_id=user_id,
            pile_id=pile_id,
            target_amount=float(amount),
            pile_power=pile.power,
            request_id=request_id,
        )
        session.start()
        self.active_sessions[session.session_id] = session
        self.user_active_session[user_id] = session.session_id
        self.pile_active_session[pile_id] = session.session_id
        pile_management_service.mark_charging(pile_id, session.session_id)
        return session

    def get_session(self, session_id: str):
        return self.active_sessions.get(session_id) or self.completed_sessions.get(session_id)

    def get_user_active_session(self, user_id: str):
        session_id = self.user_active_session.get(user_id)
        if not session_id:
            return None
        session = self.active_sessions.get(session_id)
        if session:
            session.refresh_progress()
        return session

    def get_pile_active_session(self, pile_id: str):
        session_id = self.pile_active_session.get(pile_id)
        return self.active_sessions.get(session_id) if session_id else None

    def end_session(self, session_id: str, reason: str = "manual stop"):
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError("active session not found")
        session.refresh_progress()
        if session.status != "COMPLETED":
            session.stop(reason)
        self._archive_session(session)
        pile_management_service.add_statistics(session.pile_id, session.current_amount, session.duration_hours())
        pile_management_service.mark_available(session.pile_id)
        bill = billing_service.create_bill(session)
        return session, bill

    def close_completed_sessions(self):
        closed = []
        for session_id, session in list(self.active_sessions.items()):
            session.refresh_progress()
            if session.status == "COMPLETED":
                self._archive_session(session)
                pile_management_service.add_statistics(session.pile_id, session.current_amount, session.duration_hours())
                pile_management_service.mark_available(session.pile_id)
                bill = billing_service.create_bill(session)
                closed.append((session, bill))
        return closed

    def list_user_sessions(self, user_id: str):
        items = [s for s in self.completed_sessions.values() if s.user_id == user_id]
        active = self.get_user_active_session(user_id)
        if active:
            items.insert(0, active)
        return sorted(items, key=lambda s: s.start_time or s.end_time, reverse=True)

    def list_active_sessions(self):
        for session in self.active_sessions.values():
            session.refresh_progress()
        return list(self.active_sessions.values())

    def list_all_sessions(self):
        sessions = list(self.active_sessions.values()) + list(self.completed_sessions.values())
        for session in sessions:
            session.refresh_progress()
        return sorted(sessions, key=lambda s: s.start_time or s.end_time, reverse=True)

    def get_statistics(self):
        from services.billing_service import billing_service
        bills = billing_service.list_all_bills()
        return {
            "activeSessions": len(self.active_sessions),
            "completedSessions": len(self.completed_sessions),
            "totalSessions": len(self.active_sessions) + len(self.completed_sessions),
            "totalEnergy": round(sum(bill.energy_amount for bill in bills), 2),
            "totalCost": round(sum(bill.total_fee for bill in bills), 2),
        }

    def _archive_session(self, session: ChargingSession):
        self.active_sessions.pop(session.session_id, None)
        self.user_active_session.pop(session.user_id, None)
        self.pile_active_session.pop(session.pile_id, None)
        self.completed_sessions[session.session_id] = session


charging_session_service = ChargingSessionService()
