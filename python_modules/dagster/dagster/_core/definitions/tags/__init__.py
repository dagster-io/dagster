from typing import Optional

from .tag_set import NamespacedTagSet as NamespacedTagSet


class StorageKindTagSet(NamespacedTagSet):
    """Tag entries which describe how an asset is stored.

    Args:
        storage_kind (Optional[str]): The storage type of the asset.
            For example, "snowflake" or "s3".
    """

    storage_kind: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster"
