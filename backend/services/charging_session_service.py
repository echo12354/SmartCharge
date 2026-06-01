"""Charging session service."""

from models.charging_session import ChargingSession
from repositories.session_repository import SessionRepository
from services.billing_service import billing_service
from services.pile_management_service import pile_management_service


class ChargingSessionService:
    def __init__(self):
        self.active_sessions: dict[str, ChargingSession] = {}
        self.completed_sessions: dict[str, ChargingSession] = {}
        self.user_active_session: dict[str, str] = {}
        self.pile_active_session: dict[str, str] = {}
        self.repository = SessionRepository()
        self._load_active_sessions_from_database()

    def create_and_start(self, user_id: str, pile_id: str, amount: float, request_id: str | None = None):
        active = self.get_user_active_session(user_id)
        if active:
            return active
        pile_active = self.get_pile_active_session(pile_id)
        if pile_active:
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
        self._save_session_to_database(session)
        pile_management_service.mark_charging(pile_id, session.session_id)
        return session

    def get_session(self, session_id: str):
        session = self._get_session_from_database(session_id)
        if session:
            self._cache_session(session)
            return session
        return self.active_sessions.get(session_id) or self.completed_sessions.get(session_id)

    def get_user_active_session(self, user_id: str):
        session_id = self.user_active_session.get(user_id)
        session = self.active_sessions.get(session_id) if session_id else None
        if not session:
            session = self._get_active_session_by_user_from_database(user_id)
            if session:
                self._cache_session(session)
        if session:
            session.refresh_progress()
            self._save_session_to_database(session)
        return session

    def get_pile_active_session(self, pile_id: str):
        session_id = self.pile_active_session.get(pile_id)
        session = self.active_sessions.get(session_id) if session_id else None
        if not session:
            session = self._get_active_session_by_pile_from_database(pile_id)
            if session:
                self._cache_session(session)
        return session

    def end_session(self, session_id: str, reason: str = "manual stop"):
        session = self.active_sessions.get(session_id) or self._get_session_from_database(session_id)
        if not session:
            raise ValueError("active session not found")
        if session.status not in ("PREPARING", "CHARGING"):
            raise ValueError("active session not found")
        session.refresh_progress()
        if session.status != "COMPLETED":
            session.stop(reason)
        self._save_session_to_database(session)
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
                self._save_session_to_database(session)
                self._archive_session(session)
                pile_management_service.add_statistics(session.pile_id, session.current_amount, session.duration_hours())
                pile_management_service.mark_available(session.pile_id)
                bill = billing_service.create_bill(session)
                closed.append((session, bill))
        return closed

    def list_user_sessions(self, user_id: str):
        sessions = self._list_user_sessions_from_database(user_id)
        if sessions is not None:
            for session in sessions:
                self._cache_session(session)
            return sessions
        items = [s for s in self.completed_sessions.values() if s.user_id == user_id]
        active = self.get_user_active_session(user_id)
        if active:
            items.insert(0, active)
        return sorted(items, key=lambda s: s.start_time or s.end_time, reverse=True)

    def list_active_sessions(self):
        sessions = self._list_active_sessions_from_database()
        if sessions is not None:
            for session in sessions:
                session.refresh_progress()
                self._cache_session(session)
                self._save_session_to_database(session)
            return sessions
        for session in self.active_sessions.values():
            session.refresh_progress()
        return list(self.active_sessions.values())

    def list_all_sessions(self):
        sessions = self._list_all_sessions_from_database()
        if sessions is not None:
            for session in sessions:
                self._cache_session(session)
            return sessions
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

    def _load_active_sessions_from_database(self):
        sessions = self._list_active_sessions_from_database()
        if sessions is None:
            return
        for session in sessions:
            self._cache_session(session)

    def _cache_session(self, session: ChargingSession):
        if session.status in ("PREPARING", "CHARGING"):
            self.active_sessions[session.session_id] = session
            self.user_active_session[session.user_id] = session.session_id
            self.pile_active_session[session.pile_id] = session.session_id
        else:
            self.active_sessions.pop(session.session_id, None)
            self.user_active_session.pop(session.user_id, None)
            self.pile_active_session.pop(session.pile_id, None)
            self.completed_sessions[session.session_id] = session

    def _save_session_to_database(self, session: ChargingSession):
        try:
            self.repository.save_session(session)
        except Exception:
            pass

    def _get_session_from_database(self, session_id: str):
        try:
            return self.repository.get_session(session_id)
        except Exception:
            return None

    def _get_active_session_by_user_from_database(self, user_id: str):
        try:
            return self.repository.get_active_session_by_user(user_id)
        except Exception:
            return None

    def _get_active_session_by_pile_from_database(self, pile_id: str):
        try:
            return self.repository.get_active_session_by_pile(pile_id)
        except Exception:
            return None

    def _list_active_sessions_from_database(self):
        try:
            return self.repository.list_active_sessions()
        except Exception:
            return None

    def _list_user_sessions_from_database(self, user_id: str):
        try:
            return self.repository.list_user_sessions(user_id)
        except Exception:
            return None

    def _list_all_sessions_from_database(self):
        try:
            return self.repository.list_all_sessions()
        except Exception:
            return None


charging_session_service = ChargingSessionService()
