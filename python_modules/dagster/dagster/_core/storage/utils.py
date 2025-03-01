from enum import Enum

from dagster._core.storage.event_log.schema import AssetKeyTable


class AssetKeyOrdering(Enum):
    DEFAULT = "DEFAULT"
    LAST_MATERIALIZATION_TIMESTMAP_ASC = "LAST_MATERIALIZATION_TIMESTMAP_ASC"
    LAST_MATERIALIZATION_TIMESTMAP_DESC = "LAST_MATERIALIZATION_TIMESTMAP_DESC"

    def to_db_order_by(self):
        if self == AssetKeyOrdering.LAST_MATERIALIZATION_TIMESTMAP_ASC:
            return AssetKeyTable.c.last_materialization_timestamp.asc()
        elif self == AssetKeyOrdering.LAST_MATERIALIZATION_TIMESTMAP_DESC:
            return AssetKeyTable.c.last_materialization_timestamp.desc()
        else:
            return AssetKeyTable.c.asset_key.asc()
