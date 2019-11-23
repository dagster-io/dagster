import time

import pytest

from dagster import seven
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster.core.events.log import DagsterEventRecord
from dagster.core.storage.event_log import (
    EventLogInvalidForRun,
    InMemoryEventLogStorage,
    SqliteEventLogStorage,
)
from dagster.core.storage.event_log.sqlite.sqlite_event_log import (
    CREATE_EVENT_LOG_SQL,
    INSERT_EVENT_SQL,
)


def test_in_memory_event_log_storage_run_not_found():
    storage = InMemoryEventLogStorage()
    assert storage.get_logs_for_run('bar') == []


def test_in_memory_event_log_storage_store_events_and_wipe():
    storage = InMemoryEventLogStorage()
    assert len(storage.get_logs_for_run('foo')) == 0
    storage.store_event(
        DagsterEventRecord(
            None,
            'Message2',
            'debug',
            '',
            'foo',
            time.time(),
            dagster_event=DagsterEvent(
                DagsterEventType.ENGINE_EVENT.value,
                'nonce',
                event_specific_data=EngineEventData.in_process(999),
            ),
        )
    )
    assert len(storage.get_logs_for_run('foo')) == 1
    storage.wipe()
    assert len(storage.get_logs_for_run('foo')) == 0


def test_filesystem_event_log_storage_run_not_found():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        assert storage.get_logs_for_run('bar') == []


def test_filesystem_event_log_storage_store_events_and_wipe():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        assert len(storage.get_logs_for_run('foo')) == 0
        storage.store_event(
            DagsterEventRecord(
                None,
                'Message2',
                'debug',
                '',
                'foo',
                time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    'nonce',
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )
        assert len(storage.get_logs_for_run('foo')) == 1
        storage.wipe()
        assert len(storage.get_logs_for_run('foo')) == 0


def test_event_log_delete():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        assert len(storage.get_logs_for_run('foo')) == 0
        storage.store_event(
            DagsterEventRecord(
                None,
                'Message2',
                'debug',
                '',
                'foo',
                time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ENGINE_EVENT.value,
                    'nonce',
                    event_specific_data=EngineEventData.in_process(999),
                ),
            )
        )
        assert len(storage.get_logs_for_run('foo')) == 1
        storage.delete_events('foo')
        assert len(storage.get_logs_for_run('foo')) == 0


def test_filesystem_event_log_storage_run_corrupted():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        with open(storage.filepath_for_run_id('foo'), 'w') as fd:
            fd.write('some nonsense')
        with pytest.raises(EventLogInvalidForRun) as exc:
            storage.get_logs_for_run('foo')
        assert exc.value.run_id == 'foo'


def test_filesystem_event_log_storage_run_corrupted_bad_data():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        with storage._connect('foo') as conn:  # pylint: disable=protected-access
            conn.cursor().execute(CREATE_EVENT_LOG_SQL)
            conn.cursor().execute(INSERT_EVENT_SQL, ('{bar}', None, None))
        with pytest.raises(EventLogInvalidForRun) as exc:
            storage.get_logs_for_run('foo')
        assert exc.value.run_id == 'foo'

        with storage._connect('bar') as conn:  # pylint: disable=protected-access
            conn.cursor().execute(CREATE_EVENT_LOG_SQL)
            conn.cursor().execute(INSERT_EVENT_SQL, ('3', None, None))
        with pytest.raises(EventLogInvalidForRun) as exc:
            storage.get_logs_for_run('bar')
        assert exc.value.run_id == 'bar'
