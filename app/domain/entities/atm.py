import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict

from app.exceptions.exceptions import ATMCashError


@dataclass
class ATM:
    """Represents the physical ATM state and cash inventory."""
    # Denominations mapping, e.g., {'100': 10} means 10 bills of $100
    denominations: Dict[str, int] = field(default_factory=dict)
    atm_id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def total_cash(self) -> Decimal:
        """Calculates the total cash available in the ATM."""
        return sum(
            (Decimal(denom) * count for denom, count in self.denominations.items()), 
            Decimal("0.00")
        )

    def refill(self, new_denominations: Dict[str, int]) -> None:
        """Adds cash to the ATM inventory."""
        for denom, count in new_denominations.items():
            if count < 0:
                raise ValueError(f"Cannot add negative count for denomination {denom}")
            if denom in self.denominations:
                self.denominations[denom] += count
            else:
                self.denominations[denom] = count

    def can_dispense(self, amount: Decimal) -> bool:
        """Checks if the ATM can dispense the requested amount with current denominations."""
        try:
            self._calculate_dispense_mix(amount)
            return True
        except ATMCashError:
            return False

    def dispense(self, amount: Decimal) -> Dict[str, int]:
        """Dispenses cash by updating inventory and returning the mix of bills."""
        mix = self._calculate_dispense_mix(amount)
        for denom, count in mix.items():
            self.denominations[denom] -= count
        return mix

    def _calculate_dispense_mix(self, amount: Decimal) -> Dict[str, int]:
        """Core logic to determine the combination of bills to dispense."""
        if amount <= Decimal("0.00"):
            raise ValueError("Dispense amount must be positive.")

        if amount > self.total_cash:
            raise ATMCashError("ATM has insufficient total cash.")

        mix: Dict[str, int] = {}
        remaining = amount

        # Sort denominations descending (e.g., '100', '50', '20', '10')
        sorted_denoms = sorted(
            [d for d in self.denominations.keys() if self.denominations[d] > 0],
            key=lambda x: Decimal(x),
            reverse=True
        )

        for denom_str in sorted_denoms:
            if remaining <= 0:
                break
                
            denom_val = Decimal(denom_str)
            available_notes = self.denominations[denom_str]
            
            if denom_val <= remaining:
                needed_notes = int(remaining // denom_val)
                notes_to_take = min(needed_notes, available_notes)
                
                if notes_to_take > 0:
                    mix[denom_str] = notes_to_take
                    remaining -= denom_val * notes_to_take

        if remaining > Decimal("0.00"):
            raise ATMCashError("Cannot dispense this exact amount with current denominations.")

        return mix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atm_id": str(self.atm_id),
            "denominations": self.denominations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ATM":
        return cls(
            atm_id=uuid.UUID(data["atm_id"]),
            denominations=data.get("denominations", {}),
        )