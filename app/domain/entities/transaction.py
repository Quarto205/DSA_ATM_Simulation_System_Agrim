import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


@dataclass
class Transaction:
    """Represents an immutable record of a financial transaction."""
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    description: str
    transaction_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": str(self.transaction_id),
            "account_id": str(self.account_id),
            "transaction_type": self.transaction_type.value,
            "amount": str(self.amount),
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            transaction_id=uuid.UUID(data["transaction_id"]),
            account_id=uuid.UUID(data["account_id"]),
            transaction_type=TransactionType(data["transaction_type"]),
            amount=Decimal(data["amount"]),
            description=data["description"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )