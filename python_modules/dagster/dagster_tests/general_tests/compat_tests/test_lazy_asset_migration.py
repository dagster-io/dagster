# pylint: disable=protected-access
import os

from dagster import file_relative_path
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.storage.event_log.sql_event_log import (
    SECONDARY_INDEX_ASSET_KEY,
    SqlEventLogStorage,
)
from dagster.utils.test import copy_directory


def test_event_log_asset_key_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_9_22_lazy_asset_index_migration/sqlite")
    with copy_directory(src_dir) as test_dir:
        instance = DagsterInstance.from_ref(
            InstanceRef.from_dir(
                test_dir,
                overrides={
                    "event_log_storage": {
                        "module": "dagster.core.storage.event_log.sqlite.consolidated_sqlite_event_log",
                        "class": "ConsolidatedSqliteEventLogStorage",
                        "config": {"base_dir": os.path.join(test_dir, "history")},
                    }
                },
            )
        )

        # ensure everything is upgraded
        instance.upgrade()

        assert isinstance(instance._event_storage, SqlEventLogStorage)
        assert not instance._event_storage.has_secondary_index(SECONDARY_INDEX_ASSET_KEY)

        old_keys = instance.all_asset_keys()

        assert instance._event_storage.has_secondary_index(SECONDARY_INDEX_ASSET_KEY)

        new_keys = instance.all_asset_keys()

        assert set(old_keys) == set(new_keys)
