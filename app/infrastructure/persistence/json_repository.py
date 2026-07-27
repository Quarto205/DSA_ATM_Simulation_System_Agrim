import json
from pathlib import Path
from typing import TypeVar, Generic, List, Optional, Callable, Any, Type, Dict

from app.domain.interfaces.repository import Repository

T = TypeVar('T')


class JsonRepository(Repository[T]):
    """
    A generic repository implementation that persists domain entities to a JSON file.
    """

    def __init__(self, file_path: Path | str, entity_class: Type[T], id_field_name: str):
        """
        :param file_path: Path to the JSON file where data is stored.
        :param entity_class: The class of the entity (e.g., Account, Card).
        :param id_field_name: The name of the ID field in the serialized dict (e.g., 'account_id').
        """
        self._file_path = Path(file_path)
        self._entity_class = entity_class
        self._id_field = id_field_name
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Creates the file and its parent directories if they don't exist."""
        if not self._file_path.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_data(self) -> List[Dict[str, Any]]:
        """Reads and parses the JSON file."""
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the file is empty or corrupted, return an empty list
            return []

    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """Writes data back to the JSON file safely."""
        with open(self._file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """Retrieves an entity by its unique identifier."""
        records = self._load_data()
        entity_id_str = str(entity_id)
        
        for record in records:
            if str(record.get(self._id_field)) == entity_id_str:
                # Use the class's from_dict method to reconstruct the entity
                return self._entity_class.from_dict(record)
        return None

    def get_all(self) -> List[T]:
        """Retrieves all entities."""
        records = self._load_data()
        return [self._entity_class.from_dict(record) for record in records]

    def save(self, entity: T) -> None:
        """Saves a new entity or updates an existing one (Upsert)."""
        records = self._load_data()
        
        # We rely on the entity having a to_dict() method
        entity_dict = entity.to_dict()  # type: ignore
        entity_id_str = str(entity_dict[self._id_field])

        updated = False
        for i, record in enumerate(records):
            if str(record.get(self._id_field)) == entity_id_str:
                records[i] = entity_dict
                updated = True
                break

        if not updated:
            records.append(entity_dict)

        self._save_data(records)

    def delete(self, entity_id: Any) -> None:
        """Deletes an entity by its unique identifier."""
        records = self._load_data()
        entity_id_str = str(entity_id)
        
        # Keep all records EXCEPT the one with the matching ID
        filtered_records = [
            record for record in records 
            if str(record.get(self._id_field)) != entity_id_str
        ]
        
        # Only write to disk if something was actually removed
        if len(records) != len(filtered_records):
            self._save_data(filtered_records)

    def find(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Finds entities that match a given condition.
        Useful for queries like: repo.find(lambda c: c.card_number == "1234")
        """
        all_entities = self.get_all()
        return [entity for entity in all_entities if predicate(entity)]