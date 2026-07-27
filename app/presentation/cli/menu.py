from decimal import Decimal, InvalidOperation
from typing import Optional
import uuid

from app.application.services.admin_service import AdminService
from app.application.services.authentication_service import AuthenticationService
from app.application.services.bank_service import BankService
from app.domain.entities.receipt import Receipt
from app.domain.entities.session import Session, Role
from app.exceptions.exceptions import ATMException


class ATMCLI:
    """
    Command Line Interface for the ATM Simulation System.
    """

    def __init__(
        self,
        auth_service: AuthenticationService,
        bank_service: BankService,
        admin_service: AdminService
    ):
        self.auth_service = auth_service
        self.bank_service = bank_service
        self.admin_service = admin_service
        self.current_session: Optional[Session] = None

    def run(self) -> None:
        """Main loop of the CLI application."""
        while True:
            try:
                if not self.current_session:
                    self._show_main_menu()
                elif self.current_session.role == Role.CUSTOMER:
                    self._show_customer_menu()
                elif self.current_session.role == Role.ADMIN:
                    self._show_admin_menu()
            except KeyboardInterrupt:
                print("\nExiting ATM System. Goodbye!")
                break
            except Exception as e:
                print(f"\n[!] Unexpected Error: {e}")

    # --- MENUS ---

    def _show_main_menu(self) -> None:
        print("\n" + "="*30)
        print("    WELCOME TO THE ATM")
        print("="*30)
        print("1. Insert Card (Customer Login)")
        print("2. Admin Login")
        print("3. Open New Account")
        print("4. Exit")
        
        choice = input("Select an option: ").strip()
        
        if choice == '1':
            self._handle_customer_login()
        elif choice == '2':
            self._handle_admin_login()
        elif choice == '3':
            self._handle_open_account()
        elif choice == '4':
            print("Thank you for using our ATM. Goodbye!")
            exit(0)
        else:
            print("[!] Invalid option. Please try again.")

    def _show_customer_menu(self) -> None:
        print("\n" + "="*30)
        print("       CUSTOMER MENU")
        print("="*30)
        print("1. Check Balance")
        print("2. Withdraw Cash")
        print("3. Deposit Cash")
        print("4. Transfer Funds")
        print("5. Mini Statement")
        print("6. Logout")
        
        choice = input("Select an option: ").strip()
        
        try:
            if choice == '1':
                self._handle_balance_inquiry()
            elif choice == '2':
                self._handle_withdrawal()
            elif choice == '3':
                self._handle_deposit()
            elif choice == '4':
                self._handle_transfer()
            elif choice == '5':
                self._handle_mini_statement()
            elif choice == '6':
                self._handle_logout()
            else:
                print("[!] Invalid option. Please try again.")
        except ATMException as e:
            print(f"\n[!] Transaction Failed: {e}")

    def _show_admin_menu(self) -> None:
        print("\n" + "="*30)
        print("         ADMIN MENU")
        print("="*30)
        print("1. View ATM Cash Inventory")
        print("2. Refill ATM")
        print("3. Unlock Customer Card")
        print("4. View All Accounts")
        print("5. View System Transactions")
        print("6. Logout")
        
        choice = input("Select an option: ").strip()
        
        try:
            if choice == '1':
                self._handle_view_inventory()
            elif choice == '2':
                self._handle_refill_atm()
            elif choice == '3':
                self._handle_unlock_card()
            elif choice == '4':
                self._handle_view_accounts()
            elif choice == '5':
                self._handle_view_transactions()
            elif choice == '6':
                self._handle_logout()
            else:
                print("[!] Invalid option. Please try again.")
        except ATMException as e:
            print(f"\n[!] Admin Action Failed: {e}")

    # --- LOGIN & LOGOUT ---

    def _handle_customer_login(self) -> None:
        card_number = input("Enter Card Number: ").strip()
        pin = input("Enter PIN: ").strip()
        try:
            self.current_session = self.auth_service.login_customer(card_number, pin)
            print("\n[*] Login successful!")
        except ATMException as e:
            print(f"\n[!] Login failed: {e}")

    def _handle_admin_login(self) -> None:
        username = input("Enter Admin Username: ").strip()
        pin = input("Enter Admin PIN: ").strip()
        try:
            self.current_session = self.auth_service.login_admin(username, pin)
            print("\n[*] Admin login successful!")
        except ATMException as e:
            print(f"\n[!] Login failed: {e}")

    def _handle_open_account(self) -> None:
        print("\n" + "="*30)
        print("       OPEN NEW ACCOUNT")
        print("="*30)
        pin = input("Set a 4-digit PIN: ").strip()
        initial_deposit = self._get_decimal_input("Initial Deposit Amount: $")
        
        if initial_deposit is None:
            return
            
        try:
            acc_num, card_num = self.admin_service.open_new_account(pin, initial_deposit)
            print("\n[*] Account Created Successfully!")
            print(f"    Account Number: {acc_num}")
            print(f"    Card Number:    {card_num}")
            print("    (Please save your Card Number and PIN to login!)")
        except Exception as e:
            print(f"\n[!] Failed to create account: {e}")

    def _handle_logout(self) -> None:
        if self.current_session:
            self.auth_service.logout(self.current_session.session_id)
            self.current_session = None
            print("\n[*] Logged out successfully.")

    # --- CUSTOMER OPERATIONS ---

    def _handle_balance_inquiry(self) -> None:
        assert self.current_session is not None
        balance = self.bank_service.get_balance(self.current_session.user_id)
        print(f"\n[*] Your current balance is: ${balance:.2f}")

    def _handle_withdrawal(self) -> None:
        assert self.current_session is not None
        amount = self._get_decimal_input("Enter withdrawal amount: $")
        if not amount: return

        tx = self.bank_service.withdraw(self.current_session.user_id, amount)
        balance = self.bank_service.get_balance(self.current_session.user_id)
        print("\n[*] Please take your cash.")
        self._print_receipt("12345678", tx.transaction_type.value, tx.amount, balance, tx.transaction_id)

    def _handle_deposit(self) -> None:
        assert self.current_session is not None
        amount = self._get_decimal_input("Enter deposit amount: $")
        if not amount: return

        tx = self.bank_service.deposit(self.current_session.user_id, amount)
        balance = self.bank_service.get_balance(self.current_session.user_id)
        print("\n[*] Cash deposited successfully.")
        self._print_receipt("12345678", tx.transaction_type.value, tx.amount, balance, tx.transaction_id)

    def _handle_transfer(self) -> None:
        assert self.current_session is not None
        to_account = input("Enter destination account number: ").strip()
        amount = self._get_decimal_input("Enter transfer amount: $")
        if not amount: return

        tx = self.bank_service.transfer(self.current_session.user_id, to_account, amount)
        balance = self.bank_service.get_balance(self.current_session.user_id)
        print("\n[*] Transfer successful.")
        self._print_receipt("12345678", tx.transaction_type.value, tx.amount, balance, tx.transaction_id)

    def _handle_mini_statement(self) -> None:
        assert self.current_session is not None
        transactions = self.bank_service.get_mini_statement(self.current_session.user_id)
        balance = self.bank_service.get_balance(self.current_session.user_id)
        
        print("\n" + "="*30)
        print("       MINI STATEMENT")
        print("="*30)
        if not transactions:
            print("No recent transactions.")
        else:
            for tx in transactions:
                date_str = tx.timestamp.strftime('%Y-%m-%d %H:%M')
                print(f"{date_str} | {tx.transaction_type.value[:8]:<8} | ${tx.amount:.2f}")
        print("-" * 30)
        print(f"Current Balance: ${balance:.2f}")
        print("="*30)

    def _print_receipt(self, acct_num: str, tx_type: str, amount: Decimal, balance: Decimal, tx_id: uuid.UUID) -> None:
        generate = input("Would you like a receipt? (y/n): ").strip().lower()
        if generate == 'y':
            receipt = Receipt(
                account_number=acct_num,
                transaction_type=tx_type,
                amount=amount,
                balance_after=balance,
                transaction_id=tx_id
            )
            print("\n" + receipt.generate_text())

    # --- ADMIN OPERATIONS ---

    def _handle_view_inventory(self) -> None:
        inventory = self.admin_service.view_atm_inventory()
        total = sum(Decimal(k) * v for k, v in inventory.items())
        print("\n" + "="*30)
        print("      ATM CASH INVENTORY")
        print("="*30)
        for denom, count in sorted(inventory.items(), key=lambda x: Decimal(x[0]), reverse=True):
            print(f"${denom:<4} bills : {count}")
        print("-" * 30)
        print(f"TOTAL CASH: ${total:.2f}")
        print("="*30)

    def _handle_refill_atm(self) -> None:
        print("\n--- Refill ATM ---")
        print("Enter counts for each denomination (press Enter to skip a denomination)")
        denoms = ["100", "50", "20", "10"]
        refill_mix = {}
        for d in denoms:
            count_str = input(f"Number of ${d} bills to add: ").strip()
            if count_str.isdigit():
                refill_mix[d] = int(count_str)
                
        if refill_mix:
            self.admin_service.refill_atm(refill_mix)
            print("\n[*] ATM successfully refilled.")
        else:
            print("\n[*] No cash added.")

    def _handle_unlock_card(self) -> None:
        card_num = input("Enter Card Number to unlock: ").strip()
        self.admin_service.unlock_card(card_num)
        print(f"\n[*] Card {card_num} has been unlocked successfully.")

    def _handle_view_accounts(self) -> None:
        accounts = self.admin_service.get_all_accounts()
        print("\n" + "="*40)
        print("          ALL ACCOUNTS")
        print("="*40)
        for acc in accounts:
            print(f"Acct: {acc.account_number} | Bal: ${acc.balance:.2f} | ID: {str(acc.account_id)[:8]}")
        print("="*40)

    def _handle_view_transactions(self) -> None:
        transactions = self.admin_service.get_all_transactions()
        print("\n" + "="*60)
        print("               SYSTEM TRANSACTIONS (Latest 20)")
        print("="*60)
        for tx in transactions[:20]:
            date_str = tx.timestamp.strftime('%Y-%m-%d %H:%M')
            print(f"{date_str} | {tx.transaction_type.value[:10]:<10} | ${tx.amount:<8.2f} | Acct: {str(tx.account_id)[:8]}")
        print("="*60)

    # --- HELPERS ---

    def _get_decimal_input(self, prompt: str) -> Optional[Decimal]:
        """Safely gets decimal input from the user."""
        val = input(prompt).strip()
        try:
            return Decimal(val)
        except InvalidOperation:
            print("[!] Invalid amount format. Please enter numbers only.")
            return None