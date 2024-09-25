from typing import Optional

from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet


class DbtMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to dbt objects.

    Args:
        materialization_type (Optional[str]): The materialization type, like "table" or "view". See
            https://docs.getdbt.com/docs/build/materializations.
    """

    materialization_type: Optional[str]

    @classmethod
    def namespace(cls) -> str:
        return "dagster-dbt"
