import json
import os
import re
from pathlib import Path
from typing import Any

import dagster as dg


class WebhookStorageResource(dg.ConfigurableResource):
    """Resource for accessing webhook payload storage.

    This resource reads webhook payloads stored by the webhook server.
    The webhook server and Dagster share a common storage directory.

    For testing, override this resource with a mock implementation.
    """

    storage_dir: str = "/tmp/webhook_storage"

    def _ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists."""
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)

    def _sanitize_source_id(self, source_id: str) -> str:
        """Sanitize source_id to prevent path traversal attacks."""
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", source_id)
        if not sanitized:
            raise ValueError("Invalid source_id: must contain valid filename characters")
        return sanitized

    def _get_source_file(self, source_id: str) -> Path:
        """Get the file path for a source's payloads with path traversal protection."""
        safe_id = self._sanitize_source_id(source_id)
        source_file = Path(self.storage_dir) / f"{safe_id}.json"

        resolved_path = source_file.resolve()
        resolved_storage = Path(self.storage_dir).resolve()

        if not str(resolved_path).startswith(str(resolved_storage) + os.sep):
            raise ValueError("Invalid source_id: path traversal detected")

        return resolved_path

    def get_pending_payloads(self, source_id: str) -> list[dict[str, Any]]:
        """Get pending webhook payloads for a source.

        Args:
            source_id: The source identifier

        Returns:
            List of pending payloads
        """
        self._ensure_storage_dir()
        source_file = self._get_source_file(source_id)

        if not source_file.exists():
            return []

        with open(source_file) as f:
            return json.load(f)

    def clear_payloads(self, source_id: str) -> None:
        """Clear all payloads for a source after processing.

        Args:
            source_id: The source identifier
        """
        source_file = self._get_source_file(source_id)
        if source_file.exists():
            source_file.unlink()

    def get_all_sources(self) -> dict[str, list[dict[str, Any]]]:
        """Get all webhook payloads from all sources.

        Returns:
            Dictionary mapping source_id to list of payloads
        """
        self._ensure_storage_dir()
        storage: dict[str, list[dict[str, Any]]] = {}

        for source_file in Path(self.storage_dir).glob("*.json"):
            source_id = source_file.stem
            with open(source_file) as f:
                storage[source_id] = json.load(f)

        return storage
