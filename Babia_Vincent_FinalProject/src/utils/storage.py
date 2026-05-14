"""
storage.py
----------
Handles all JSON-based file persistence for the Finance Tracker.

Uses a context-manager pattern and provides atomic write semantics so data is
never left in a partially-written state.

Intermediate concepts demonstrated:
  - Context managers (with statement)
  - JSON serialization / deserialization
  - Exception handling with custom messages
  - Path management via pathlib
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


# Default storage location relative to the project root
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_DB_FILE = DEFAULT_DATA_DIR / "finance_data.json"


class StorageError(Exception):
    """Raised when a read or write operation on the data store fails."""


class JSONStorage:
    """
    Thin wrapper around a single JSON file used as a simple data store.

    The store keeps a root dict with arbitrary keys. The Finance Tracker uses
    the key ``"transactions"`` to hold a list of serialised Transaction dicts.

    Attributes:
        filepath (Path): Absolute path to the JSON file.
    """

    def __init__(self, filepath: Path = DEFAULT_DB_FILE):
        """
        Initialise storage and ensure the parent directory exists.

        Args:
            filepath: Path to the target JSON file.
        """
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Create an empty store if the file does not exist yet
        if not self.filepath.exists():
            self._write({"transactions": [], "budgets": {}})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """
        Read and return the entire data store as a dictionary.

        Returns:
            Parsed JSON content.

        Raises:
            StorageError: If the file cannot be read or parsed.
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise StorageError(f"Corrupted data file: {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Cannot read data file: {exc}") from exc

    def save(self, data: dict) -> None:
        """
        Persist *data* to disk atomically (write-then-rename).

        Writing to a temp file first ensures the original is never left half-
        written if the process is interrupted.

        Args:
            data: Dictionary to serialise.

        Raises:
            StorageError: If the write fails.
        """
        try:
            self._write(data)
        except OSError as exc:
            raise StorageError(f"Cannot write data file: {exc}") from exc

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a single top-level key from the store.

        Args:
            key: Key to look up.
            default: Value returned when the key is absent.

        Returns:
            The stored value or *default*.
        """
        return self.load().get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Update a single top-level key and persist immediately.

        Args:
            key: Key to update.
            value: JSON-serialisable value.
        """
        data = self.load()
        data[key] = value
        self.save(data)

    def backup(self) -> Path:
        """
        Create a timestamped backup of the data file next to the original.

        Returns:
            Path to the backup file.
        """
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.filepath.parent / f"finance_data_backup_{stamp}.json"
        shutil.copy2(self.filepath, backup_path)
        return backup_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write(self, data: dict) -> None:
        """Write *data* to disk using a temp-file-then-rename strategy."""
        dir_ = self.filepath.parent
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            shutil.move(tmp_path, self.filepath)
        except Exception:
            # Clean up the temp file if anything goes wrong
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
