import hashlib
import uuid
from typing import Optional

from app.domain.entities.admin import Admin
from app.domain.entities.card import Card
from app.domain.entities.session import Session, Role
from app.domain.interfaces.repository import Repository
from app.exceptions.exceptions import AccountLockedError, ATMException


class AuthenticationService:
    """
    Handles authentication, session creation, and security lockouts.
    """

    def __init__(
        self,
        card_repository: Repository[Card],
        admin_repository: Repository[Admin],
        session_repository: Repository[Session]
    ):
        self.card_repository = card_repository
        self.admin_repository = admin_repository
        self.session_repository = session_repository

    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hashes a PIN using SHA-256 for secure comparison."""
        return hashlib.sha256(pin.encode('utf-8')).hexdigest()

    def login_customer(self, card_number: str, pin: str) -> Session:
        """Authenticates a customer and returns an active session."""
        cards = self.card_repository.find(lambda c: c.card_number == card_number)
        
        if not cards:
            raise ATMException("Invalid card number or PIN.")
            
        card = cards[0]

        # Check if card is already locked
        card.check_access()

        # Validate PIN
        if card.pin_hash != self.hash_pin(pin):
            card.record_failed_attempt()
            self.card_repository.save(card)
            
            if card.is_locked:
                raise AccountLockedError("Too many failed attempts. Card is now locked.")
            raise ATMException("Invalid card number or PIN.")

        # Successful login: reset attempts and save state
        card.reset_failed_attempts()
        self.card_repository.save(card)

        # Create and persist a new session
        session = Session(user_id=card.account_id, role=Role.CUSTOMER)
        self.session_repository.save(session)
        
        return session

    def login_admin(self, username: str, pin: str) -> Session:
        """Authenticates an administrator."""
        admins = self.admin_repository.find(lambda a: a.username == username)
        
        if not admins:
            raise ATMException("Invalid admin credentials.")
            
        admin = admins[0]

        if admin.pin_hash != self.hash_pin(pin):
            raise ATMException("Invalid admin credentials.")

        session = Session(user_id=admin.admin_id, role=Role.ADMIN)
        self.session_repository.save(session)
        
        return session

    def logout(self, session_id: uuid.UUID) -> None:
        """Ends an active session."""
        session = self.session_repository.get_by_id(session_id)
        if session and session.is_active:
            session.end_session()
            self.session_repository.save(session)