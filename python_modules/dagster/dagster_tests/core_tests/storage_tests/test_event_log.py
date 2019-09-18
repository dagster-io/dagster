import time

import pytest

from dagster import seven
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster.core.events.log import DagsterEventRecord
from dagster.core.storage.event_log import (
    INSERT_EVENT_SQL,
    EventLogInvalidForRun,
    EventLogNotFoundForRun,
    FilesystemEventLogStorage,
    InMemoryEventLogStorage,
)


def test_in_memory_event_log_storage_init():
    storage = InMemoryEventLogStorage()
    assert storage.is_persistent is False


def test_in_memory_event_log_storage_new_run():
    storage = InMemoryEventLogStorage()
    storage.new_run('foo')
    assert storage.has_run('foo')
    assert storage.get_logs_for_run('foo') == []


def test_in_memory_event_log_storage_run_not_found():
    storage = InMemoryEventLogStorage()
    assert not storage.has_run('bar')
    with pytest.raises(EventLogNotFoundForRun) as exc:
        storage.get_logs_for_run('bar')
    assert exc.value.run_id == 'bar'


def test_in_memory_event_log_storage_store_events_and_wipe():
    storage = InMemoryEventLogStorage()
    storage.new_run('foo')
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
    assert not storage.has_run('foo')
    with pytest.raises(EventLogNotFoundForRun) as exc:
        storage.get_logs_for_run('foo')
    assert exc.value.run_id == 'foo'


def test_filesystem_event_log_storage_init():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = FilesystemEventLogStorage(tmpdir_path)
        assert storage.is_persistent


def test_filesystem_event_log_storage_new_run():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = FilesystemEventLogStorage(tmpdir_path)
        storage.new_run('foo')
        assert storage.has_run('foo')
        assert storage.get_logs_for_run('foo') == []


def test_filesystem_event_log_storage_run_not_found():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = FilesystemEventLogStorage(tmpdir_path)
        assert not storage.has_run('bar')
        with pytest.raises(EventLogNotFoundForRun) as exc:
            storage.get_logs_for_run('bar')
        assert exc.value.run_id == 'bar'


def test_filesystem_event_log_storage_store_events_and_wipe():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = FilesystemEventLogStorage(tmpdir_path)
        storage.new_run('foo')
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
        assert not storage.has_run('foo')
        with pytest.raises(EventLogNotFoundForRun) as exc:
            storage.get_logs_for_run('foo')
        assert exc.value.run_id == 'foo'


def test_filesystem_event_log_storage_run_corrupted():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = FilesystemEventLogStorage(tmpdir_path)
        with open(storage.filepath_for_run_id('foo'), 'w') as fd:
            fd.write('some nonsense')
        assert storage.has_run('foo')
        with pytest.raises(EventLogInvalidForRun) as exc:
            storage.get_logs_for_run('foo')
        assert exc.value.run_id == 'foo'


def test_filesystem_event_log_storage_run_corrupted_bad_data():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = FilesystemEventLogStorage(tmpdir_path)
        storage.new_run('foo')
        with storage._connect('foo') as conn:  # pylint: disable=protected-access
            conn.cursor().execute(INSERT_EVENT_SQL, ('{bar}',))
        assert storage.has_run('foo')
        with pytest.raises(EventLogInvalidForRun) as exc:
            storage.get_logs_for_run('foo')
        assert exc.value.run_id == 'foo'

        storage.new_run('bar')
        with storage._connect('bar') as conn:  # pylint: disable=protected-access
            conn.cursor().execute(INSERT_EVENT_SQL, ('3',))
        assert storage.has_run('bar')
        with pytest.raises(EventLogInvalidForRun) as exc:
            storage.get_logs_for_run('bar')
        assert exc.value.run_id == 'bar'
