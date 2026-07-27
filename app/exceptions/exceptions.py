class ATMException(Exception):
    """Base exception for all ATM related errors."""
    pass


class InsufficientFundsError(ATMException):
    """Raised when an account does not have enough funds for a transaction."""
    pass


class AccountLockedError(ATMException):
    """Raised when attempting an operation on a locked account."""
    pass


class InvalidAmountError(ATMException):
    """Raised when a transaction amount is invalid (e.g., negative or zero)."""
    pass


class ATMCashError(ATMException):
    """Raised when the ATM cannot fulfill a cash request (insufficient cash or bad denominations)."""
    pass