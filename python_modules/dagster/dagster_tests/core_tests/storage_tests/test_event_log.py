import os
import time

import pytest
import sqlalchemy

from dagster import seven
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster.core.events.log import DagsterEventRecord
from dagster.core.storage.event_log import (
    DagsterEventLogInvalidForRun,
    InMemoryEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
    SqliteEventLogStorage,
)
from dagster.core.storage.sql import create_engine


def test_init_in_memory_event_log_storage():
    storage = InMemoryEventLogStorage()
    assert not storage.is_persistent


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
    assert storage.get_stats_for_run('foo')
    storage.wipe()
    assert len(storage.get_logs_for_run('foo')) == 0


def test_in_memory_event_log_storage_watch():
    def evt(name):
        return DagsterEventRecord(
            None,
            name,
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

    watched = []
    watcher = lambda x: watched.append(x)  # pylint: disable=unnecessary-lambda

    storage = InMemoryEventLogStorage()
    assert len(storage.get_logs_for_run('foo')) == 0

    storage.store_event(evt('Message1'))
    assert len(storage.get_logs_for_run('foo')) == 1
    assert len(watched) == 0

    storage.watch('foo', None, watcher)
    storage.store_event(evt('Message2'))
    assert len(storage.get_logs_for_run('foo')) == 2
    assert len(watched) == 1

    storage.end_watch('foo', lambda event: None)
    storage.store_event(evt('Message3'))
    assert len(storage.get_logs_for_run('foo')) == 3
    assert len(watched) == 2

    storage.end_watch('bar', lambda event: None)
    storage.store_event(evt('Message4'))
    assert len(storage.get_logs_for_run('foo')) == 4
    assert len(watched) == 3

    storage.end_watch('foo', watcher)
    storage.store_event(evt('Message5'))
    assert len(storage.get_logs_for_run('foo')) == 5
    assert len(watched) == 3

    storage.delete_events('foo')
    assert len(storage.get_logs_for_run('foo')) == 0
    assert len(watched) == 3


def test_init_filesystem_event_log_storage():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        assert storage.is_persistent


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


def test_filesystem_event_log_storage_watch():
    def evt(name):
        return DagsterEventRecord(
            None,
            name,
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

    watched = []

    def callback(evt):
        watched.append(evt)

    noop = lambda evt: None

    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)

        assert len(storage.get_logs_for_run('foo')) == 0

        storage.store_event(evt('Message1'))
        assert len(storage.get_logs_for_run('foo')) == 1
        assert len(watched) == 0

        storage.watch('foo', 2, callback)
        storage.store_event(evt('Message2'))
        assert len(storage.get_logs_for_run('foo')) == 2

        storage.end_watch('foo', noop)
        storage.store_event(evt('Message3'))
        assert len(storage.get_logs_for_run('foo')) == 3

        storage.end_watch('bar', noop)
        storage.store_event(evt('Message4'))
        assert len(storage.get_logs_for_run('foo')) == 4

        time.sleep(0.5)  # this value scientifically selected from a range of attractive values
        storage.end_watch('foo', callback)
        time.sleep(0.5)
        storage.store_event(evt('Message5'))
        assert len(storage.get_logs_for_run('foo')) == 5
        assert len(watched) == 3

        storage.delete_events('foo')
        assert len(storage.get_logs_for_run('foo')) == 0
        assert len(watched) == 3


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
        assert storage.get_stats_for_run('foo')
        storage.delete_events('foo')
        assert len(storage.get_logs_for_run('foo')) == 0


def test_filesystem_event_log_storage_run_corrupted():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        # URL begins sqlite:///
        # pylint: disable=protected-access
        with open(os.path.abspath(storage.conn_string_for_run_id('foo')[10:]), 'w') as fd:
            fd.write('some nonsense')
        with pytest.raises(sqlalchemy.exc.DatabaseError):
            storage.get_logs_for_run('foo')


def test_filesystem_event_log_storage_run_corrupted_bad_data():
    with seven.TemporaryDirectory() as tmpdir_path:
        storage = SqliteEventLogStorage(tmpdir_path)
        SqlEventLogStorageMetadata.create_all(create_engine(storage.conn_string_for_run_id('foo')))
        with storage.connect('foo') as conn:
            event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id='foo', event='{bar}', dagster_event_type=None, timestamp=None
            )
            conn.execute(event_insert)

        with pytest.raises(DagsterEventLogInvalidForRun):
            storage.get_logs_for_run('foo')

        SqlEventLogStorageMetadata.create_all(create_engine(storage.conn_string_for_run_id('bar')))

        with storage.connect('bar') as conn:  # pylint: disable=protected-access
            event_insert = SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id='bar', event='3', dagster_event_type=None, timestamp=None
            )
            conn.execute(event_insert)
        with pytest.raises(DagsterEventLogInvalidForRun):
            storage.get_logs_for_run('bar')
