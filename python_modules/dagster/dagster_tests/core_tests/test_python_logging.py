import logging

import pytest
from dagster import (
    ModeDefinition,
    execute_pipeline,
    fs_io_manager,
    pipeline,
    reconstructable,
    resource,
    solid,
)
from dagster.core.test_utils import instance_for_test


def get_log_records(pipe, managed_loggers=None, python_logging_level=None, run_config=None):
    python_logs_overrides = {}
    if managed_loggers is not None:
        python_logs_overrides["managed_python_loggers"] = managed_loggers
    if python_logging_level is not None:
        python_logs_overrides["python_log_level"] = python_logging_level

    overrides = {}
    if python_logs_overrides:
        overrides["python_logs"] = python_logs_overrides

    with instance_for_test(overrides=overrides) as instance:
        result = execute_pipeline(pipe, instance=instance)
        event_records = instance.event_log_storage.get_logs_for_run(result.run_id)
    return [er for er in event_records if er.user_message]


@pytest.mark.parametrize(
    "managed_logs,expect_output",
    [
        (None, False),
        (["root"], True),
        (["python_logger"], True),
        (["some_logger"], False),
        (["root", "python_logger"], True),
    ],
)
def test_logging_capture_logger_defined_outside(managed_logs, expect_output):
    logger = logging.getLogger("python_logger")
    logger.setLevel(logging.INFO)

    @solid
    def my_solid():
        logger.info("some info")

    @pipeline
    def my_pipeline():
        my_solid()

    log_event_records = [
        lr for lr in get_log_records(my_pipeline, managed_logs) if lr.user_message == "some info"
    ]

    if expect_output:
        assert len(log_event_records) == 1
        log_event_record = log_event_records[0]
        assert log_event_record.step_key == "my_solid"
        assert log_event_record.level == logging.INFO
    else:
        assert len(log_event_records) == 0


@pytest.mark.parametrize(
    "managed_logs,expect_output",
    [
        (None, False),
        (["root"], True),
        (["python_logger"], True),
        (["some_logger"], False),
        (["root", "python_logger"], True),
    ],
)
def test_logging_capture_logger_defined_inside(managed_logs, expect_output):
    @solid
    def my_solid():
        logger = logging.getLogger("python_logger")
        logger.setLevel(logging.INFO)
        logger.info("some info")

    @pipeline
    def my_pipeline():
        my_solid()

    log_event_records = [
        lr for lr in get_log_records(my_pipeline, managed_logs) if lr.user_message == "some info"
    ]

    if expect_output:
        assert len(log_event_records) == 1
        log_event_record = log_event_records[0]
        assert log_event_record.step_key == "my_solid"
        assert log_event_record.level == logging.INFO
    else:
        assert len(log_event_records) == 0


@pytest.mark.parametrize(
    "managed_logs,expect_output",
    [
        (None, False),
        (["root"], True),
        (["python_logger"], True),
        (["some_logger"], False),
        (["root", "python_logger"], True),
    ],
)
def test_logging_capture_resource(managed_logs, expect_output):

    python_log = logging.getLogger("python_logger")
    python_log.setLevel(logging.DEBUG)

    @resource
    def foo_resource():
        def fn():
            python_log.info("log from resource foo")

        return fn

    @resource
    def bar_resource():
        def fn():
            python_log.info("log from resource bar")

        return fn

    @solid(required_resource_keys={"foo", "bar"})
    def process(context):
        context.resources.foo()
        context.resources.bar()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"foo": foo_resource, "bar": bar_resource})])
    def my_pipeline():
        process()

    log_event_records = [
        lr
        for lr in get_log_records(my_pipeline, managed_logs)
        if lr.user_message.startswith("log from resource")
    ]

    if expect_output:
        assert len(log_event_records) == 2
        log_event_record = log_event_records[0]
        assert log_event_record.level == logging.INFO
    else:
        assert len(log_event_records) == 0


@pytest.mark.parametrize(
    "log_level,expected_msgs",
    [
        (None, 3),  # default python log level is WARNING
        ("DEBUG", 5),
        ("INFO", 4),
        ("WARNING", 3),
        ("ERROR", 2),
        ("CRITICAL", 1),
    ],
)
def test_logging_capture_level_defined_outside(log_level, expected_msgs):
    logger = logging.getLogger("python_logger_outside")

    @solid
    def my_solid():
        for level in [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]:
            logger.log(level=level, msg="logger_foobarbaz")

    @pipeline
    def my_pipeline():
        my_solid()

    records = get_log_records(
        my_pipeline, managed_loggers=["python_logger_outside"], python_logging_level=log_level
    )
    python_logger_records = [r for r in records if r.user_message == "logger_foobarbaz"]

    assert len(python_logger_records) == expected_msgs


@pytest.mark.parametrize(
    "log_level,expected_msgs",
    [
        (None, 3),  # default python log level is WARNING
        ("DEBUG", 5),
        ("INFO", 4),
        ("WARNING", 3),
        ("ERROR", 2),
        ("CRITICAL", 1),
    ],
)
def test_logging_capture_level_defined_inside(log_level, expected_msgs):
    @solid
    def my_solid():
        logger = logging.getLogger("python_logger_inside")
        for level in [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]:
            logger.log(level=level, msg="foobarbaz")

    @pipeline
    def my_pipeline():
        my_solid()

    log_event_records = [
        lr
        for lr in get_log_records(
            my_pipeline, managed_loggers=["root"], python_logging_level=log_level
        )
        if lr.user_message == "foobarbaz"
    ]

    assert len(log_event_records) == expected_msgs


def define_logging_pipeline():
    loggerA = logging.getLogger("loggerA")

    @solid
    def solidA():
        loggerA.debug("loggerA")
        loggerA.info("loggerA")
        return 1

    @solid
    def solidB(_in):
        loggerB = logging.getLogger("loggerB")
        loggerB.debug("loggerB")
        loggerB.info("loggerB")
        loggerA.debug("loggerA")
        loggerA.info("loggerA")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
    def pipe():
        solidB(solidA())

    return pipe


@pytest.mark.parametrize("managed_loggers", [["root"], ["loggerA", "loggerB"]])
def test_multiprocess_logging(managed_loggers):

    log_records = get_log_records(
        reconstructable(define_logging_pipeline),
        managed_loggers=managed_loggers,
        python_logging_level="INFO",
        run_config={
            "execution": {"multiprocess": {}},
        },
    )

    logA_records = [lr for lr in log_records if lr.user_message == "loggerA"]
    logB_records = [lr for lr in log_records if lr.user_message == "loggerB"]

    assert len(logA_records) == 2
    assert len(logB_records) == 1
