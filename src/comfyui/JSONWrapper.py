import json
from typing import Any, Dict

class JSONWrapper:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        """Load JSON data from the file."""
        try:
            with open(self.filepath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"File {self.filepath} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.filepath}.")
            return {}

    def _write_json(self) -> None:
        """Write the current data back to the JSON file."""
        try:
            with open(self.filepath, 'w') as file:
                json.dump(self.data, file, indent=4)
        except Exception as e:
            print(f"An error occurred while writing to {self.filepath}: {e}")

    def get_entry(self, key: str) -> Dict[str, Any]:
        """Get a specific entry from the JSON data."""
        return self.data.get(key, {})

    def update_entry(self, key: str, value: Dict[str, Any]) -> None:
        """Update a specific entry in the JSON data."""
        self.data[key] = value
        self._write_json()

    def add_entry(self, key: str, value: Dict[str, Any]) -> None:
        """Add a new entry to the JSON data."""
        if key in self.data:
            print(f"Key {key} already exists. Use update_entry to update it.")
            return
        self.update_entry(key, value)

    def remove_entry(self, key: str) -> None:
        """Remove an entry from the JSON data."""
        if key in self.data:
            del self.data[key]
            self._write_json()
        else:
            print(f"Key {key} not found.")
