from typing import Optional

from .tag_set import NamespacedTagSet as NamespacedTagSet


class StorageKindTagSet(NamespacedTagSet):
    """Metadata entries which describe how an asset is stored."""

    storage_kind: Optional[str]

    @classmethod
    def namespace(cls) -> str:
        return "dagster"
