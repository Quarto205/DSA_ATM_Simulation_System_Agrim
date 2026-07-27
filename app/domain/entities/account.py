import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict

from app.exceptions.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
)


@dataclass
class Account:
    account_number: str
    account_id: uuid.UUID = field(default_factory=uuid.uuid4)
    balance: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def deposit(self, amount: Decimal) -> None:
        if amount <= Decimal("0.00"):
            raise InvalidAmountError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount: Decimal) -> None:
        if amount <= Decimal("0.00"):
            raise InvalidAmountError("Withdrawal amount must be positive.")
            
        if amount > self.balance:
            raise InsufficientFundsError("Insufficient funds for this withdrawal.")
            
        self.balance -= amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": str(self.account_id),
            "account_number": self.account_number,
            "balance": str(self.balance),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            account_id=uuid.UUID(data["account_id"]),
            account_number=data["account_number"],
            balance=Decimal(data["balance"]),
        )