import uuid
from decimal import Decimal
from typing import List

from app.application.services.cash_service import CashService
from app.domain.entities.account import Account
from app.domain.entities.transaction import Transaction, TransactionType
from app.domain.interfaces.repository import Repository
from app.exceptions.exceptions import ATMException, ATMCashError


class BankService:
    """
    Orchestrates core banking operations: deposits, withdrawals, and transfers.
    """

    def __init__(
        self,
        account_repository: Repository[Account],
        transaction_repository: Repository[Transaction],
        cash_service: CashService
    ):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.cash_service = cash_service

    def _get_account(self, account_id: uuid.UUID) -> Account:
        account = self.account_repository.get_by_id(account_id)
        if not account:
            raise ATMException("Account not found.")
        return account

    def get_balance(self, account_id: uuid.UUID) -> Decimal:
        """Retrieves the current balance of the account."""
        account = self._get_account(account_id)
        return account.balance

    def get_mini_statement(self, account_id: uuid.UUID, limit: int = 5) -> List[Transaction]:
        """Retrieves the most recent transactions for an account."""
        transactions = self.transaction_repository.find(lambda t: t.account_id == account_id)
        # Sort descending by timestamp and limit
        transactions.sort(key=lambda t: t.timestamp, reverse=True)
        return transactions[:limit]

    def deposit(self, account_id: uuid.UUID, amount: Decimal) -> Transaction:
        """Processes a cash deposit."""
        account = self._get_account(account_id)
        
        # Domain logic handles validation
        account.deposit(amount)
        
        # Record Transaction
        transaction = Transaction(
            account_id=account.account_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            description="ATM Cash Deposit"
        )
        
        # Persist changes
        self.account_repository.save(account)
        self.transaction_repository.save(transaction)
        
        return transaction

    def withdraw(self, account_id: uuid.UUID, amount: Decimal) -> Transaction:
        """Processes a cash withdrawal, coordinating with the ATM hardware."""
        account = self._get_account(account_id)
        
        # 1. Check if the physical ATM has the right mix of bills BEFORE debiting the account
        if not self.cash_service.check_availability(amount):
            raise ATMCashError("ATM cannot dispense this exact amount. Try different multiples.")
            
        # 2. Debit the account (Domain logic checks for sufficient funds)
        account.withdraw(amount)
        
        # 3. Dispense the physical cash (Updates ATM inventory)
        self.cash_service.dispense_cash(amount)
        
        # 4. Record Transaction
        transaction = Transaction(
            account_id=account.account_id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            description="ATM Cash Withdrawal"
        )
        
        # 5. Persist changes
        self.account_repository.save(account)
        self.transaction_repository.save(transaction)
        
        return transaction

    def transfer(self, from_account_id: uuid.UUID, to_account_number: str, amount: Decimal) -> Transaction:
        """Transfers funds from one account to another."""
        source_account = self._get_account(from_account_id)
        
        # Find destination account
        target_accounts = self.account_repository.find(lambda a: a.account_number == to_account_number)
        if not target_accounts:
            raise ATMException(f"Destination account {to_account_number} not found.")
        target_account = target_accounts[0]
        
        if source_account.account_id == target_account.account_id:
            raise ATMException("Cannot transfer to the same account.")
            
        # Domain logic execution
        source_account.withdraw(amount)
        target_account.deposit(amount)
        
        # Record Transactions for both parties
        tx_out = Transaction(
            account_id=source_account.account_id,
            transaction_type=TransactionType.TRANSFER_OUT,
            amount=amount,
            description=f"Transfer to {to_account_number}"
        )
        tx_in = Transaction(
            account_id=target_account.account_id,
            transaction_type=TransactionType.TRANSFER_IN,
            amount=amount,
            description=f"Transfer from {source_account.account_number}"
        )
        
        # Persist changes
        self.account_repository.save(source_account)
        self.account_repository.save(target_account)
        self.transaction_repository.save(tx_out)
        self.transaction_repository.save(tx_in)
        
        return tx_out