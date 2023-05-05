import logging
from typing import Mapping, Optional, Sequence, Union

import mock
import pytest
from dagster import get_dagster_logger, reconstructable, resource
from dagster._core.definitions.decorators import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import instance_for_test


def _reset_logging() -> None:
    logging.root = logging.RootLogger(logging.WARNING)
    logging.Logger.root = logging.root
    logging.Logger.manager = logging.Manager(logging.Logger.root)


@pytest.fixture
def reset_logging():
    _reset_logging()
    try:
        yield
    finally:
        _reset_logging()


def get_log_records(
    job_def: Union[JobDefinition, ReconstructableJob],
    managed_loggers: Optional[Sequence[str]] = None,
    python_logging_level: Optional[str] = None,
    run_config: Optional[Mapping[str, object]] = None,
):
    python_logs_overrides = {}
    if managed_loggers is not None:
        python_logs_overrides["managed_python_loggers"] = managed_loggers
    if python_logging_level is not None:
        python_logs_overrides["python_log_level"] = python_logging_level

    overrides = {}
    if python_logs_overrides:
        overrides["python_logs"] = python_logs_overrides

    with instance_for_test(overrides=overrides) as instance:
        if isinstance(job_def, JobDefinition):
            result = job_def.execute_in_process(run_config=run_config, instance=instance)
        else:
            result = execute_job(job_def, instance=instance, run_config=run_config)
        assert result.success
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
def test_logging_capture_logger_defined_outside(managed_logs, expect_output, reset_logging):
    logger = logging.getLogger("python_logger")
    logger.setLevel(logging.INFO)

    @op
    def my_op():
        logger.info("some info")

    @job
    def my_job():
        my_op()

    log_event_records = [
        lr for lr in get_log_records(my_job, managed_logs) if lr.user_message == "some info"
    ]

    if expect_output:
        assert len(log_event_records) == 1
        log_event_record = log_event_records[0]
        assert log_event_record.step_key == "my_op"
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
def test_logging_capture_logger_defined_inside(managed_logs, expect_output, reset_logging):
    @op
    def my_op():
        logger = logging.getLogger("python_logger")
        logger.setLevel(logging.INFO)
        logger.info("some info")

    @job
    def my_job():
        my_op()

    log_event_records = [
        lr for lr in get_log_records(my_job, managed_logs) if lr.user_message == "some info"
    ]

    if expect_output:
        assert len(log_event_records) == 1
        log_event_record = log_event_records[0]
        assert log_event_record.step_key == "my_op"
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
def test_logging_capture_resource(managed_logs, expect_output, reset_logging):
    python_log = logging.getLogger("python_logger")
    python_log.setLevel(logging.DEBUG)

    @resource
    def foo_resource():
        def fn():
            python_log.info("log from resource %s", "foo")

        return fn

    @resource
    def bar_resource():
        def fn():
            python_log.info("log from resource %s", "bar")

        return fn

    @op(required_resource_keys={"foo", "bar"})
    def process(context):
        context.resources.foo()
        context.resources.bar()

    @job(resource_defs={"foo": foo_resource, "bar": bar_resource})
    def my_job():
        process()

    log_event_records = [
        lr
        for lr in get_log_records(my_job, managed_logs)
        if lr.user_message.startswith("log from resource")
    ]

    if expect_output:
        assert len(log_event_records) == 2
        log_event_record = log_event_records[0]
        assert log_event_record.level == logging.INFO
    else:
        assert len(log_event_records) == 0


def define_multilevel_logging_job(inside: bool, python: bool) -> JobDefinition:
    if not inside:
        outside_logger = logging.getLogger("my_logger_outside") if python else get_dagster_logger()

    @op
    def my_op1():
        if inside:
            logger = logging.getLogger("my_logger_inside") if python else get_dagster_logger()
        else:
            logger = outside_logger
        for level in [
            logging.DEBUG,
            logging.INFO,
        ]:
            logger.log(level, "foobar%s", "baz")

    @op
    def my_op2(_in):
        if inside:
            logger = logging.getLogger("my_logger_inside") if python else get_dagster_logger()
        else:
            logger = outside_logger
        for level in [
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]:
            logger.log(level=level, msg="foobarbaz")

    @job
    def my_job():
        my_op2(my_op1())

    return my_job


def multilevel_logging_python_inside():
    return define_multilevel_logging_job(inside=True, python=True)


def multilevel_logging_python_outside():
    return define_multilevel_logging_job(inside=False, python=True)


def multilevel_logging_builtin_inisde():
    return define_multilevel_logging_job(inside=True, python=False)


def multilevel_logging_builtin_outside():
    return define_multilevel_logging_job(inside=False, python=False)


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
def test_logging_capture_level_defined_outside(log_level, expected_msgs, reset_logging):
    log_event_records = [
        lr
        for lr in get_log_records(
            multilevel_logging_python_outside(),
            managed_loggers=["my_logger_outside"],
            python_logging_level=log_level,
        )
        if lr.user_message == "foobarbaz"
    ]

    assert len(log_event_records) == expected_msgs


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
def test_logging_capture_level_defined_inside(log_level, expected_msgs, reset_logging):
    log_event_records = [
        lr
        for lr in get_log_records(
            multilevel_logging_python_inside(),
            managed_loggers=["my_logger_inside"],
            python_logging_level=log_level,
        )
        if lr.user_message == "foobarbaz"
    ]

    assert len(log_event_records) == expected_msgs


@pytest.mark.parametrize(
    "log_level,expected_msgs",
    [
        ("DEBUG", 5),
        ("INFO", 4),
        ("WARNING", 3),
        ("ERROR", 2),
        ("CRITICAL", 1),
    ],
)
def test_logging_capture_builtin_outside(log_level, expected_msgs, reset_logging):
    log_event_records = [
        lr
        for lr in get_log_records(
            multilevel_logging_builtin_outside(), python_logging_level=log_level
        )
        if lr.user_message == "foobarbaz"
    ]

    assert len(log_event_records) == expected_msgs


@pytest.mark.parametrize(
    "log_level,expected_msgs",
    [
        ("DEBUG", 5),
        ("INFO", 4),
        ("WARNING", 3),
        ("ERROR", 2),
        ("CRITICAL", 1),
    ],
)
def test_logging_capture_builtin_inside(log_level, expected_msgs, reset_logging):
    log_event_records = [
        lr
        for lr in get_log_records(
            multilevel_logging_builtin_inisde(), python_logging_level=log_level
        )
        if lr.user_message == "foobarbaz"
    ]

    assert len(log_event_records) == expected_msgs


def define_logging_job():
    loggerA = logging.getLogger("loggerA")

    @op
    def opA():
        loggerA.debug("loggerA")
        loggerA.info("loggerA")
        return 1

    @op
    def opB(_in):
        loggerB = logging.getLogger("loggerB")
        loggerB.debug("loggerB")
        loggerB.info("loggerB")
        loggerA.debug("loggerA")
        loggerA.info("loggerA")

    @job
    def foo_job():
        opB(opA())

    return foo_job


@pytest.mark.parametrize(
    "managed_loggers,run_config",
    [
        (["root"], None),
        (
            ["root"],
            {
                "execution": {"config": {"multiprocess": {}}},
            },
        ),
        (
            ["loggerA", "loggerB"],
            {
                "execution": {"config": {"multiprocess": {}}},
            },
        ),
    ],
)
def test_execution_logging(managed_loggers, run_config, reset_logging):
    log_records = get_log_records(
        reconstructable(define_logging_job),
        managed_loggers=managed_loggers,
        python_logging_level="INFO",
        run_config=run_config,
    )

    logA_records = [lr for lr in log_records if lr.user_message == "loggerA"]
    logB_records = [lr for lr in log_records if lr.user_message == "loggerB"]

    assert len(logA_records) == 2
    assert len(logB_records) == 1


@pytest.mark.parametrize("managed_loggers", [["root"], ["loggerA", "loggerB"]])
def test_failure_logging(managed_loggers, reset_logging):
    with instance_for_test(
        overrides={
            "python_logs": {
                "managed_python_loggers": managed_loggers,
                "python_log_level": "INFO",
            }
        }
    ) as instance:
        result = execute_job(
            reconstructable(define_logging_job),
            run_config={"execution": {"config": {"in_process": {}}}},
            instance=instance,
        )
        assert result.success
        event_records = instance.event_log_storage.get_logs_for_run(result.run_id)

        num_user_events = len(
            [log_record for log_record in event_records if not log_record.dagster_event]
        )
        assert num_user_events > 0

        # Now make all user log calls fail
        orig_handle_new_event = instance.handle_new_event

        # run still succeeds even if user-generated logger writes fail
        def _fake_handle_new_event(event):
            # fail all user-generated log calls
            if not event.dagster_event:
                raise Exception("failed writing user-generated event")

            return orig_handle_new_event(event)

        with mock.patch.object(instance, "handle_new_event", _fake_handle_new_event):
            result = execute_job(
                reconstructable(define_logging_job),
                run_config={"execution": {"config": {"in_process": {}}}},
                instance=instance,
            )
            assert result.success
            event_records = instance.event_log_storage.get_logs_for_run(result.run_id)

            assert (
                len([log_record for log_record in event_records if not log_record.dagster_event])
                == 0
            )

            # Each user event is now replaced with an event log explaining that the write failed
            assert (
                len(
                    [
                        log_record
                        for log_record in event_records
                        if "Exception while writing logger call to event log" in log_record.message
                    ]
                )
                == num_user_events
            )

        # If system events fail, the whole run does fail
        with mock.patch.object(
            instance, "handle_new_event", side_effect=Exception("failed writing event")
        ):
            with pytest.raises(Exception, match="failed writing event"):
                execute_job(
                    reconstructable(define_logging_job),
                    run_config={"execution": {"config": {"in_process": {}}}},
                    instance=instance,
                )
