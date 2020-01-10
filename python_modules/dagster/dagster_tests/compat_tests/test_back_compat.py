# pylint: disable=protected-access
import os
import re

import pytest

from dagster import file_relative_path
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.utils.test import restore_directory


# test that we can load runs and events from an old instance
def test_0_6_4():
    test_dir = file_relative_path(__file__, 'snapshot_0_6_4')
    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        runs = instance.get_runs()
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


def test_0_6_6_sqlite_exc():
    test_dir = file_relative_path(__file__, 'snapshot_0_6_6/sqlite')
    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        runs = instance.get_runs()
        # Note that this is a deliberate choice -- old runs are simply invisible, and their
        # presence won't raise DagsterInstanceMigrationRequired. This is a reasonable choice since
        # the runs.db has moved and otherwise we would have to do a check for the existence of an
        # old runs.db every time we accessed the runs. Instead, we'll do this only in the upgrade
        # method.
        assert len(runs) == 0

        run_ids = instance._event_storage.get_all_run_ids()
        assert run_ids == ['89296095-892d-4a15-aa0d-9018d1580945']

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=re.escape(
                'Instance is out of date and must be migrated (SqliteEventLogStorage for run '
                '89296095-892d-4a15-aa0d-9018d1580945). Database is at revision None, head is '
                '567bc23fd1ac. Please run `dagster instance migrate`.'
            ),
        ):
            instance._event_storage.get_logs_for_run('89296095-892d-4a15-aa0d-9018d1580945')


def test_0_6_6_sqlite_migrate():
    test_dir = file_relative_path(__file__, 'snapshot_0_6_6/sqlite')
    assert os.path.exists(file_relative_path(__file__, 'snapshot_0_6_6/sqlite/runs.db'))
    assert not os.path.exists(file_relative_path(__file__, 'snapshot_0_6_6/sqlite/history/runs.db'))

    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        runs = instance.get_runs()
        assert len(runs) == 1

        run_ids = instance._event_storage.get_all_run_ids()
        assert run_ids == ['89296095-892d-4a15-aa0d-9018d1580945']

        instance._event_storage.get_logs_for_run('89296095-892d-4a15-aa0d-9018d1580945')

        assert not os.path.exists(file_relative_path(__file__, 'snapshot_0_6_6/sqlite/runs.db'))
        assert os.path.exists(file_relative_path(__file__, 'snapshot_0_6_6/sqlite/history/runs.db'))
