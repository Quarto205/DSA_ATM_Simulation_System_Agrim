import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Admin:
    """Represents an administrative user in the system."""
    username: str
    pin_hash: str
    admin_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "admin_id": str(self.admin_id),
            "username": self.username,
            "pin_hash": self.pin_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Admin":
        return cls(
            admin_id=uuid.UUID(data["admin_id"]),
            username=data["username"],
            pin_hash=data["pin_hash"],
        )