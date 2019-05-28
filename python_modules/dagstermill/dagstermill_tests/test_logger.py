import logging
import multiprocessing
import os
import sqlite3
import tempfile
import threading
import uuid

from dagster import PipelineDefinition, seven
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.log_manager import DagsterLogManager
from dagster.utils.log import construct_single_handler_logger

from dagstermill.logger import init_db, JsonSqlite3Handler, JsonSqlite3LogWatcher


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
    with tempfile.NamedTemporaryFile() as sqlite3_db:
        sqlite3_db_path = sqlite3_db.name

    # Test that the handler works even if the file does not yet exist
    try:
        sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
        sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
        sqlite3_logger = sqlite3_logger_def.logger_fn(
            dummy_init_logger_context(sqlite3_logger_def, run_id)
        )
        sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

        for i in range(1000):
            sqlite3_log_manager.info('Testing ' + str(i))

        conn = sqlite3.connect(sqlite3_db_path)
        cursor = conn.cursor()
        count = cursor.execute('select count(1) from logs').fetchall()
        assert count[0][0] == 1000
    finally:
        if os.path.exists(sqlite3_db_path):
            os.unlink(sqlite3_db_path)


def test_json_sqlite3_watcher():
    test_log_records = []
    run_id = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile() as sqlite3_db:
        sqlite3_db_path = sqlite3_db.name

        sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
        sqlite3_logger_def = construct_single_handler_logger('sqlite3', 'debug', sqlite3_handler)
        sqlite3_logger = sqlite3_logger_def.logger_fn(
            dummy_init_logger_context(sqlite3_logger_def, run_id)
        )
        sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

        for i in range(1000):
            sqlite3_log_manager.info('Testing ' + str(i))

        conn = sqlite3.connect(sqlite3_db_path)
        cursor = conn.cursor()
        count = cursor.execute('select count(1) from logs').fetchall()
        assert count[0][0] == 1000

        is_done = threading.Event()
        is_done.set()

        test_handler = LogTestHandler(test_log_records)
        test_logger_def = construct_single_handler_logger('test', 'debug', test_handler)
        test_logger = test_logger_def.logger_fn(dummy_init_logger_context(test_logger_def, run_id))
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


def test_concurrent_multithreaded_logging():
    test_log_records = []
    run_id = str(uuid.uuid4())

    with tempfile.NamedTemporaryFile() as sqlite3_db:

        sqlite3_db_path = sqlite3_db.name

        is_done = threading.Event()

        def sqlite3_thread_target(sqlite3_db_path):
            sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
            sqlite3_logger_def = construct_single_handler_logger(
                'sqlite3', 'debug', sqlite3_handler
            )
            sqlite3_logger = sqlite3_logger_def.logger_fn(
                dummy_init_logger_context(sqlite3_logger_def, run_id)
            )
            sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

            for i in range(1000):
                sqlite3_log_manager.info('Testing ' + str(i))

        def test_thread_target(sqlite3_db_path, is_done):
            test_handler = LogTestHandler(test_log_records)
            test_logger_def = construct_single_handler_logger('test', 'debug', test_handler)
            test_logger = test_logger_def.logger_fn(
                dummy_init_logger_context(test_logger_def, run_id)
            )
            test_log_manager = DagsterLogManager(run_id, {}, [test_logger])
            test_log_watcher = JsonSqlite3LogWatcher(sqlite3_db_path, test_log_manager, is_done)
            test_log_watcher.watch()

        sqlite3_thread = threading.Thread(target=sqlite3_thread_target, args=(sqlite3_db_path,))

        test_thread = threading.Thread(target=test_thread_target, args=(sqlite3_db_path, is_done))

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

        conn = sqlite3.connect(sqlite3_db_path)
        cursor = conn.cursor()
        count = cursor.execute('select count(1) from logs').fetchall()
        assert count[0][0] == 1000

        records = cursor.execute('select * from logs').fetchall()
        for i, record in enumerate(records):
            json_record = record[1]
            assert json_record == seven.json.dumps(test_log_records[i].__dict__)


def test_concurrent_multiprocessing_logging():
    test_log_records = []
    run_id = str(uuid.uuid4())

    with tempfile.NamedTemporaryFile() as sqlite3_db:

        sqlite3_db_path = sqlite3_db.name

        is_done = threading.Event()

        def sqlite3_process_target(sqlite3_db_path):
            sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)
            sqlite3_logger_def = construct_single_handler_logger(
                'sqlite3', 'debug', sqlite3_handler
            )
            sqlite3_logger = sqlite3_logger_def.logger_fn(
                dummy_init_logger_context(sqlite3_logger_def, run_id)
            )
            sqlite3_log_manager = DagsterLogManager(run_id, {}, [sqlite3_logger])

            for i in range(1000):
                sqlite3_log_manager.info('Testing ' + str(i))

        def test_thread_target(sqlite3_db_path, is_done):
            test_handler = LogTestHandler(test_log_records)
            test_logger_def = construct_single_handler_logger('test', 'debug', test_handler)
            test_logger = test_logger_def.logger_fn(
                dummy_init_logger_context(test_logger_def, run_id)
            )
            test_log_manager = DagsterLogManager(run_id, {}, [test_logger])
            test_log_watcher = JsonSqlite3LogWatcher(sqlite3_db_path, test_log_manager, is_done)
            test_log_watcher.watch()

        sqlite3_process = multiprocessing.Process(
            target=sqlite3_process_target, args=(sqlite3_db_path,)
        )

        test_thread = threading.Thread(target=test_thread_target, args=(sqlite3_db_path, is_done))

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

        conn = sqlite3.connect(sqlite3_db_path)
        cursor = conn.cursor()
        count = cursor.execute('select count(1) from logs').fetchall()
        assert count[0][0] == 1000

        records = cursor.execute('select * from logs').fetchall()
        for i, record in enumerate(records):
            json_record = record[1]
            assert json_record == seven.json.dumps(test_log_records[i].__dict__)


def test_error_during_logging(caplog):
    run_id = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile() as sqlite3_db:
        sqlite3_db_path = sqlite3_db.name

        sqlite3_handler = JsonSqlite3Handler(sqlite3_db_path)

        class MockCursor:
            def execute(self, *args, **kwargs):
                raise Exception('Bailing!')

        sqlite3_handler.cursor = MockCursor()
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
