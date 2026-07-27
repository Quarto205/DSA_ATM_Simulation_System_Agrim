from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Callable, Any

# TypeVar 'T' represents our Domain Entities (Account, Card, Transaction, etc.)
T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Abstract Base Class defining the contract for all repositories.
    This ensures our services are decoupled from the specific storage mechanism.
    """

    @abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """Retrieves an entity by its unique identifier."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieves all entities from the repository."""
        pass

    @abstractmethod
    def save(self, entity: T) -> None:
        """Saves a new entity or updates an existing one."""
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> None:
        """Deletes an entity by its unique identifier."""
        pass

    @abstractmethod
    def find(self, predicate: Callable[[T], bool]) -> List[T]:
        """Finds entities that match a given condition."""
        pass