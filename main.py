import sys
from pathlib import Path

# Fix python path if running from the root directory
sys.path.append(str(Path(__file__).parent))

from app.application.services.admin_service import AdminService
from app.application.services.authentication_service import AuthenticationService
from app.application.services.bank_service import BankService
from app.application.services.cash_service import CashService

from app.domain.entities.account import Account
from app.domain.entities.admin import Admin
from app.domain.entities.atm import ATM
from app.domain.entities.card import Card
from app.domain.entities.session import Session
from app.domain.entities.transaction import Transaction

from app.infrastructure.persistence.json_repository import JsonRepository
from app.presentation.cli.menu import ATMCLI


def _seed_initial_data(
    admin_repo: JsonRepository[Admin],
    account_repo: JsonRepository[Account],
    card_repo: JsonRepository[Card]
) -> None:
    """Seeds default data if the database is completely empty."""
    # Seed default Admin
    if not admin_repo.get_all():
        default_admin = Admin(
            username="admin",
            pin_hash=AuthenticationService.hash_pin("0000")
        )
        admin_repo.save(default_admin)
        print("[*] Seeded default admin (User: admin, PIN: 0000)")

    # Seed default Customer
    if not account_repo.get_all() and not card_repo.get_all():
        default_account = Account(account_number="1001234567")
        account_repo.save(default_account)
        
        default_card = Card(
            card_number="4000123456789010",
            pin_hash=AuthenticationService.hash_pin("1234"),
            account_id=default_account.account_id
        )
        card_repo.save(default_card)
        
        # Second account to test transfers
        second_account = Account(account_number="1009876543")
        account_repo.save(second_account)
        
        print("[*] Seeded default customer (Card: 4000123456789010, PIN: 1234)")
        print(f"[*] Seeded target transfer account (Acct Num: 1009876543)")


def main() -> None:
    """Composition Root: Wire up dependencies and start the app."""
    # 1. Setup Data Directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # 2. Instantiate Repositories
    account_repo = JsonRepository(data_dir / "accounts.json", Account, "account_id")
    card_repo = JsonRepository(data_dir / "cards.json", Card, "card_id")
    transaction_repo = JsonRepository(data_dir / "transactions.json", Transaction, "transaction_id")
    atm_repo = JsonRepository(data_dir / "atm_cash.json", ATM, "atm_id")
    admin_repo = JsonRepository(data_dir / "admin.json", Admin, "admin_id")
    session_repo = JsonRepository(data_dir / "sessions.json", Session, "session_id")

    # 3. Seed Default Data (for testing ease)
    _seed_initial_data(admin_repo, account_repo, card_repo)

    # 4. Instantiate Services
    cash_service = CashService(atm_repo)
    
    auth_service = AuthenticationService(
        card_repository=card_repo,
        admin_repository=admin_repo,
        session_repository=session_repo
    )
    
    bank_service = BankService(
        account_repository=account_repo,
        transaction_repository=transaction_repo,
        cash_service=cash_service
    )
    
    admin_service = AdminService(
        card_repository=card_repo,
        account_repository=account_repo,
        transaction_repository=transaction_repo,
        cash_service=cash_service
    )

    # 5. Instantiate and Run CLI
    cli = ATMCLI(
        auth_service=auth_service,
        bank_service=bank_service,
        admin_service=admin_service
    )
    
    # 6. Start Application
    cli.run()


if __name__ == "__main__":
    main()