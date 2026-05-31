"""Charging pile management service."""

from config.settings import FAST_PILES, PILE_POWER, SLOW_PILES
from models.charging_pile import ChargingPile


class PileManagementService:
    def __init__(self):
        self.piles: dict[str, ChargingPile] = {}
        for pile_id in FAST_PILES:
            self.piles[pile_id] = ChargingPile(pile_id, "fast", PILE_POWER[pile_id])
        for pile_id in SLOW_PILES:
            self.piles[pile_id] = ChargingPile(pile_id, "slow", PILE_POWER[pile_id])

    def get_pile(self, pile_id: str) -> ChargingPile | None:
        return self.piles.get(pile_id)

    def list_piles(self):
        return list(self.piles.values())

    def power_on(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.power_on()
        return pile

    def power_off(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.power_off()
        return pile

    def start_pile(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.start()
        return pile

    def set_parameters(self, pile_id: str, parameters: dict):
        pile = self._require_pile(pile_id)
        pile.update_parameters(parameters)
        return pile

    def mark_charging(self, pile_id: str, session_id: str):
        pile = self._require_pile(pile_id)
        pile.mark_charging(session_id)
        return pile

    def mark_available(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.mark_available()
        return pile

    def mark_fault(self, pile_id: str):
        pile = self._require_pile(pile_id)
        pile.mark_fault()
        return pile

    def add_statistics(self, pile_id: str, energy: float, hours: float):
        pile = self._require_pile(pile_id)
        pile.add_statistics(energy, hours)
        return pile

    def available_piles_by_mode(self, mode: str):
        return [
            pile for pile in self.piles.values()
            if pile.pile_type == mode and pile.is_enabled and pile.status in ("ACTIVE", "CHARGING")
        ]

    def get_statistics(self):
        total = len(self.piles)
        active = sum(1 for pile in self.piles.values() if pile.is_enabled)
        charging = sum(1 for pile in self.piles.values() if pile.status == "CHARGING")
        return {
            "activePiles": active,
            "totalPiles": total,
            "chargingPiles": charging,
            "offlinePiles": total - active,
        }

    def get_reports(self):
        return [
            {
                "id": index + 1,
                "pileName": pile.pile_id,
                "timeRange": "all",
                "totalCharges": pile.total_sessions,
                "totalHours": round(pile.total_hours, 2),
                "totalEnergy": round(pile.total_energy, 2),
                "chargeFee": round(pile.total_energy * 0.7, 2),
                "serviceFee": round(pile.total_energy * 0.8, 2),
                "totalFee": round(pile.total_energy * 1.5, 2),
            }
            for index, pile in enumerate(self.list_piles())
        ]

    def _require_pile(self, pile_id: str):
        pile = self.get_pile(pile_id)
        if not pile:
            raise ValueError("pile not found")
        return pile


pile_management_service = PileManagementService()
