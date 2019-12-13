import glob
import os
import re

import pytest

from dagster import file_relative_path
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance, InstanceRef


# test that we can load runs and events from an old instance
def test_0_6_4():
    try:
        instance = DagsterInstance.from_ref(
            InstanceRef.from_dir(file_relative_path(__file__, 'snapshot_0_6_4'))
        )

        runs = instance.all_runs()
        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=re.escape(
                'Instance is out of date and must be migrated (SqliteEventLogStorage for run '
                'c7a6c4d7-6c88-46d0-8baa-d4937c3cefe5). Database is at revision None, head is '
                '567bc23fd1ac. Please run `dagster instance migrate`.'
            ),
        ):
            for run in runs:
                instance.all_logs(run.run_id)
    finally:
        for filepath in glob.glob(
            file_relative_path(
                __file__, os.path.join('snapshot_0_6_4', 'history', 'runs', '*.db-shm')
            )
        ) + glob.glob(
            file_relative_path(
                __file__, os.path.join('snapshot_0_6_4', 'history', 'runs', '*.db-wal')
            )
        ):
            os.unlink(filepath)
