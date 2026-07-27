import uuid
from dataclasses import dataclass, field
from typing import Any, Dict

from app.exceptions.exceptions import AccountLockedError


@dataclass
class Card:
    """Represents a physical ATM card used for account access."""
    card_number: str
    pin_hash: str
    account_id: uuid.UUID
    card_id: uuid.UUID = field(default_factory=uuid.uuid4)
    failed_login_attempts: int = 0
    is_locked: bool = False

    def record_failed_attempt(self, max_attempts: int = 3) -> None:
        """Records a failed PIN attempt and locks the card if threshold is met."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.is_locked = True

    def reset_failed_attempts(self) -> None:
        """Resets failed attempts upon successful login or admin unlock."""
        self.failed_login_attempts = 0
        self.is_locked = False
        
    def check_access(self) -> None:
        """Validates if the card can be used."""
        if self.is_locked:
            raise AccountLockedError("This card is locked due to too many failed attempts.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the card for persistence."""
        return {
            "card_id": str(self.card_id),
            "card_number": self.card_number,
            "pin_hash": self.pin_hash,
            "account_id": str(self.account_id),
            "failed_login_attempts": self.failed_login_attempts,
            "is_locked": self.is_locked,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Card":
        """Reconstructs the card from persistence data."""
        return cls(
            card_id=uuid.UUID(data["card_id"]),
            card_number=data["card_number"],
            pin_hash=data["pin_hash"],
            account_id=uuid.UUID(data["account_id"]),
            failed_login_attempts=data.get("failed_login_attempts", 0),
            is_locked=data.get("is_locked", False),
        )