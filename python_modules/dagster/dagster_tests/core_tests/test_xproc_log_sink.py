import logging
import multiprocessing
import os
import sqlite3
import sys
import threading
import uuid

import pytest

from dagster import PipelineDefinition, seven
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.log_manager import DagsterLogManager
from dagster.loggers.xproc_log_sink import JsonSqlite3Handler, JsonSqlite3LogWatcher, init_db
from dagster.utils import safe_tempfile_path
from dagster.utils.log import construct_single_handler_logger


class LogTestHandler(logging.Handler):
    def __init__(self, records):
        self.records = records
        super(LogTestHandler, self).__init__()

    def emit(self, record):
        self.records.append(record)


def dummy_init_logger_context(logger_def, run_id):
    return InitLoggerContext({}, PipelineDefinition([]), logger_def, run_id)


def test_json_sqlite3_handler():
    run_id = str(uuid.uuid4())
    with safe_tempfile_path() as sqlite3_db_path:
        init_db(sqlite3_db_path)

        sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
        sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
        sqlite3_logger = sqlite3_logger_def.logger_fn(
            dummy_init_logger_context(sqlite3_logger_def, run_id)
        )
        sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

        for i in range(1000):
            sqlite3_log_manager.info('Testing ' + str(i))

        with sqlite3.connect(sqlite3_db_path) as conn:
            cursor = conn.cursor()
            count = cursor.execute('select count(1) from logs').fetchall()
            assert count[0][0] == 1000
        conn.close()


def test_json_sqlite3_watcher():
    test_log_records = []
    run_id = str(uuid.uuid4())
    with safe_tempfile_path() as sqlite3_db_path:
        init_db(sqlite3_db_path)

        sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
        sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
        sqlite3_logger = sqlite3_logger_def.logger_fn(
            dummy_init_logger_context(sqlite3_logger_def, run_id)
        )
        sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

        for i in range(1000):
            sqlite3_log_manager.info('Testing ' + str(i))

        with sqlite3.connect(sqlite3_db_path) as conn:
            cursor = conn.cursor()
            count = cursor.execute('select count(1) from logs').fetchall()
            assert count[0][0] == 1000

            is_done = threading.Event()
            is_done.set()

            test_handler = LogTestHandler(test_log_records)
            test_logger_def = construct_single_handler_logger('test', 'debug', test_handler)
            test_logger = test_logger_def.logger_fn(
                dummy_init_logger_context(test_logger_def, run_id)
            )
            sqlite3_watcher_log_manager = DagsterLogManager(run_id, {}, [test_logger])
            sqlite3_watcher = JsonSqlite3LogWatcher(
                sqlite3_db_path, sqlite3_watcher_log_manager, is_done
            )

            sqlite3_watcher.watch()

            assert len(test_log_records) == 1000

            records = cursor.execute('select * from logs').fetchall()
            for i, record in enumerate(records):
                json_record = record[1]
                assert json_record == seven.json.dumps(test_log_records[i].__dict__)
        conn.close()


def thread_target_source(sqlite3_db_path, run_id):
    sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
    sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
    sqlite3_logger = sqlite3_logger_def.logger_fn(
        dummy_init_logger_context(sqlite3_logger_def, run_id)
    )
    sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

    for i in range(1000):
        sqlite3_log_manager.info('Testing ' + str(i))


def thread_target_sink(sqlite3_db_path, is_done, run_id, test_log_records):
    test_handler = LogTestHandler(test_log_records)
    test_logger_def = construct_single_handler_logger('test', 'debug', test_handler)
    test_logger = test_logger_def.logger_fn(dummy_init_logger_context(test_logger_def, run_id))
    test_log_manager = DagsterLogManager(run_id, {}, [test_logger])
    test_log_watcher = JsonSqlite3LogWatcher(sqlite3_db_path, test_log_manager, is_done)
    test_log_watcher.watch()


def test_concurrent_multithreaded_logging():
    test_log_records = []
    run_id = str(uuid.uuid4())

    with safe_tempfile_path() as sqlite3_db_path:
        is_done = threading.Event()
        sqlite3_thread = threading.Thread(
            target=thread_target_source, args=(sqlite3_db_path, run_id)
        )

        test_thread = threading.Thread(
            target=thread_target_sink, args=(sqlite3_db_path, is_done, run_id, test_log_records)
        )

        init_db(sqlite3_db_path)
        sqlite3_thread.start()
        test_thread.start()

        try:
            sqlite3_thread.join()
        finally:
            is_done.set()

        assert is_done.is_set()

        test_thread.join()
        assert len(test_log_records) == 1000

        with sqlite3.connect(sqlite3_db_path) as conn:
            cursor = conn.cursor()
            count = cursor.execute('select count(1) from logs').fetchall()
            assert count[0][0] == 1000

            records = cursor.execute('select * from logs').fetchall()
            for i, record in enumerate(records):
                json_record = record[1]
                assert json_record == seven.json.dumps(test_log_records[i].__dict__)
        conn.close()


def sqlite3_process_target(sqlite3_db_path, run_id):
    sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
    sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
    sqlite3_logger = sqlite3_logger_def.logger_fn(
        dummy_init_logger_context(sqlite3_logger_def, run_id)
    )
    sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

    for i in range(1000):
        sqlite3_log_manager.info('Testing ' + str(i))


def check_thread_target(sqlite3_db_path, is_done, run_id, test_log_records):
    test_handler = LogTestHandler(test_log_records)
    test_logger_def = construct_single_handler_logger('test', 'debug', test_handler)
    test_logger = test_logger_def.logger_fn(dummy_init_logger_context(test_logger_def, run_id))
    test_log_manager = DagsterLogManager(run_id, {}, [test_logger])
    test_log_watcher = JsonSqlite3LogWatcher(sqlite3_db_path, test_log_manager, is_done)
    test_log_watcher.watch()


# https://docs.python.org/2.7/library/multiprocessing.html#windows
@pytest.mark.skipif(
    sys.version_info >= (2, 7) and sys.version_info < (3,) and os.name == 'nt',
    reason='Special multiprocessing restrictions on py27/nt make this test setup infeasible',
)
def test_concurrent_multiprocessing_logging():
    test_log_records = []
    run_id = str(uuid.uuid4())

    with safe_tempfile_path() as sqlite3_db_path:
        is_done = threading.Event()

        sqlite3_process = multiprocessing.Process(
            target=sqlite3_process_target, args=(sqlite3_db_path, run_id)
        )

        test_thread = threading.Thread(
            target=check_thread_target, args=(sqlite3_db_path, is_done, run_id, test_log_records)
        )

        init_db(sqlite3_db_path)

        sqlite3_process.start()
        test_thread.start()

        try:
            sqlite3_process.join()
        finally:
            is_done.set()

        assert is_done.is_set()
        test_thread.join()
        assert len(test_log_records) == 1000

        with sqlite3.connect(sqlite3_db_path) as conn:
            cursor = conn.cursor()
            count = cursor.execute('select count(1) from logs').fetchall()
            assert count[0][0] == 1000

            records = cursor.execute('select * from logs').fetchall()
            for i, record in enumerate(records):
                json_record = record[1]
                assert json_record == seven.json.dumps(test_log_records[i].__dict__)
        conn.close()


def test_error_during_logging(caplog):
    run_id = str(uuid.uuid4())
    with safe_tempfile_path() as sqlite3_db_path:
        init_db(sqlite3_db_path)

        sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)

        def err_conn(*args, **kwargs):
            raise Exception('Bailing!')

        sqlite3_handler.connect = err_conn

        sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
        sqlite3_logger = sqlite3_logger_def.logger_fn(
            dummy_init_logger_context(sqlite3_logger_def, run_id)
        )
        sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

        sqlite3_log_manager.info('Testing error handling')

        assert caplog.record_tuples == [
            ('root', 50, 'Error during logging!'),
            ('root', 40, 'Bailing!'),
        ]
