from typing import List, Dict

from app.application.services.cash_service import CashService
from app.domain.entities.account import Account
from app.domain.entities.card import Card
from app.domain.entities.transaction import Transaction, TransactionType
from app.domain.interfaces.repository import Repository
from app.exceptions.exceptions import ATMException
from app.application.services.authentication_service import AuthenticationService
import random
from decimal import Decimal


class AdminService:
    """
    Handles administrative operations like unlocking cards and viewing system logs.
    """

    def __init__(
        self,
        card_repository: Repository[Card],
        account_repository: Repository[Account],
        transaction_repository: Repository[Transaction],
        cash_service: CashService
    ):
        self.card_repository = card_repository
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.cash_service = cash_service

    def unlock_card(self, card_number: str) -> None:
        """Unlocks a locked customer card."""
        cards = self.card_repository.find(lambda c: c.card_number == card_number)
        if not cards:
            raise ATMException(f"Card {card_number} not found.")
            
        card = cards[0]
        if not card.is_locked:
            raise ATMException(f"Card {card_number} is already unlocked.")
            
        card.reset_failed_attempts()
        self.card_repository.save(card)

    def get_all_accounts(self) -> List[Account]:
        """Retrieves a list of all accounts."""
        return self.account_repository.get_all()

    def get_all_transactions(self) -> List[Transaction]:
        """Retrieves the system-wide transaction ledger."""
        transactions = self.transaction_repository.get_all()
        transactions.sort(key=lambda t: t.timestamp, reverse=True)
        return transactions

    def refill_atm(self, denominations: Dict[str, int]) -> None:
        """Adds cash to the physical ATM."""
        self.cash_service.refill_atm(denominations)

    def view_atm_inventory(self) -> Dict[str, int]:
        """Checks current ATM cash inventory."""
        return self.cash_service.get_inventory()

    def open_new_account(self, pin: str, initial_deposit: Decimal) -> tuple[str, str]:
        """Generates a new account, a linked card, and processes the initial deposit."""
        acc_num = f"200{random.randint(0, 9999999):07d}"
        card_num = f"4000{random.randint(0, 999999999999):012d}"

        # 1. Create Account and Deposit initial funds
        new_account = Account(account_number=acc_num)
        if initial_deposit > Decimal("0.00"):
            new_account.deposit(initial_deposit)
            tx = Transaction(
                account_id=new_account.account_id,
                transaction_type=TransactionType.DEPOSIT,
                amount=initial_deposit,
                description="Initial Deposit"
            )
            self.transaction_repository.save(tx)
            
        self.account_repository.save(new_account)

        # 2. Create Card linked to the Account
        new_card = Card(
            card_number=card_num,
            pin_hash=AuthenticationService.hash_pin(pin),
            account_id=new_account.account_id
        )
        self.card_repository.save(new_card)

        return acc_num, card_num