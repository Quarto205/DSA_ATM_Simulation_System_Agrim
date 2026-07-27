import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class Receipt:
    """Represents a generated receipt for a transaction."""
    account_number: str
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    receipt_id: uuid.UUID = field(default_factory=uuid.uuid4)
    transaction_id: Optional[uuid.UUID] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def generate_text(self) -> str:
        """Generates the formatted textual representation of the receipt."""
        # Mask account number for security
        masked_account = f"****{self.account_number[-4:]}" if len(self.account_number) >= 4 else self.account_number
        
        return (
            f"================================\n"
            f"          ATM RECEIPT           \n"
            f"================================\n"
            f"Receipt ID: {self.receipt_id}\n"
            f"Date/Time:  {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n"
            f"Account:    {masked_account}\n"
            f"Type:       {self.transaction_type}\n"
            f"Amount:     ${self.amount:.2f}\n"
            f"Balance:    ${self.balance_after:.2f}\n"
            f"================================"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": str(self.receipt_id),
            "transaction_id": str(self.transaction_id) if self.transaction_id else None,
            "account_number": self.account_number,
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "balance_after": str(self.balance_after),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        return cls(
            receipt_id=uuid.UUID(data["receipt_id"]),
            transaction_id=uuid.UUID(data["transaction_id"]) if data.get("transaction_id") else None,
            account_number=data["account_number"],
            transaction_type=data["transaction_type"],
            amount=Decimal(data["amount"]),
            balance_after=Decimal(data["balance_after"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )