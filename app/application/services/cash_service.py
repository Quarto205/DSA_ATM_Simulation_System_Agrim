from decimal import Decimal
from typing import Dict

from app.domain.entities.atm import ATM
from app.domain.interfaces.repository import Repository
from app.exceptions.exceptions import ATMCashError


class CashService:
    """
    Manages the physical cash inventory of the ATM.
    """

    def __init__(self, atm_repository: Repository[ATM]):
        self.atm_repository = atm_repository

    def _get_atm(self) -> ATM:
        """Retrieves the single ATM instance, creating it if it doesn't exist."""
        atms = self.atm_repository.get_all()
        if not atms:
            # Initialize with default cash if system is completely fresh
            default_atm = ATM(denominations={"100": 50, "50": 50, "20": 100, "10": 100})
            self.atm_repository.save(default_atm)
            return default_atm
        return atms[0]

    def check_availability(self, amount: Decimal) -> bool:
        """Checks if the ATM can fulfill the requested amount."""
        atm = self._get_atm()
        return atm.can_dispense(amount)

    def dispense_cash(self, amount: Decimal) -> Dict[str, int]:
        """
        Dispenses cash from the ATM. 
        Should only be called after verifying account balances.
        """
        atm = self._get_atm()
        
        # The ATM entity itself throws ATMCashError if it can't dispense
        mix = atm.dispense(amount)
        
        # Persist the new state of the ATM
        self.atm_repository.save(atm)
        return mix

    def refill_atm(self, denominations: Dict[str, int]) -> None:
        """Adds physical cash to the ATM."""
        atm = self._get_atm()
        atm.refill(denominations)
        self.atm_repository.save(atm)

    def get_inventory(self) -> Dict[str, int]:
        """Returns the current denomination counts in the ATM."""
        atm = self._get_atm()
        return atm.denominations