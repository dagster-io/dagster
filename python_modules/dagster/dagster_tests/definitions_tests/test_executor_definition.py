import multiprocessing
from os import path

import dagster as dg
import pytest
from dagster import (
    DagsterInstance,
    ExecutorRequirement,
    _check as check,
    multiprocess_executor,
)
from dagster._core.definitions.executor_definition import (
    _core_multiprocess_executor_creation,
    executor,
)
from dagster._core.events import DagsterEventType, RunFailureReason
from dagster._core.execution.retries import RetryMode
from dagster._core.execution.step_dependency_config import StepDependencyConfig
from dagster._core.executor.multiprocess import MultiprocessExecutor
from dagster._core.storage.tags import RUN_FAILURE_REASON_TAG
from dagster._core.test_utils import environ


def get_job_for_executor(executor_def, execution_config=None):
    it = {}

    @dg.op
    def a_op(_):
        it["ran"] = True

    @dg.job(
        name="testing_job",
        executor_def=(
            executor_def.configured(execution_config) if execution_config else executor_def
        ),
    )
    def the_job():
        a_op()

    return the_job


def primitive_config_executor_job():
    @executor(
        name="test_executor",
        config_schema=str,
    )
    def test_executor(init_context):
        from dagster._core.executor.in_process import InProcessExecutor

        assert init_context.executor_config == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=RetryMode.from_config({"enabled": {}}),  # pyright: ignore[reportArgumentType]
            marker_to_close=None,
        )

    return get_job_for_executor(test_executor)


def test_in_process_executor_primitive_config():
    with dg.instance_for_test() as instance:
        with pytest.raises(check.ParameterCheckError):
            dg.execute_job(
                dg.reconstructable(primitive_config_executor_job),
                instance=instance,
                run_config={"execution": {"config": "secret testing value!!"}},
            )


def dict_config_executor_job():
    @executor(
        name="test_executor",
        config_schema={"value": str},
    )
    def test_executor(init_context):
        from dagster._core.executor.in_process import InProcessExecutor

        assert init_context.executor_config["value"] == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=RetryMode.from_config({"enabled": {}}),  # pyright: ignore[reportArgumentType]
            marker_to_close=None,
        )

    return get_job_for_executor(test_executor)


def test_in_process_executor_dict_config():
    with dg.instance_for_test() as instance:
        assert dg.execute_job(
            dg.reconstructable(dict_config_executor_job),
            instance=instance,
            run_config={"execution": {"config": {"value": "secret testing value!!"}}},
        ).success


def requirement_executor_job():
    @executor(
        name="test_executor",
        config_schema={"value": str},
        requirements=[ExecutorRequirement.NON_EPHEMERAL_INSTANCE],
    )
    def test_executor(init_context):
        from dagster._core.executor.in_process import InProcessExecutor

        assert init_context.executor_config["value"] == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=RetryMode.from_config({"enabled": {}}),  # pyright: ignore[reportArgumentType]
            marker_to_close=None,
        )

    return get_job_for_executor(test_executor)


def test_in_process_executor_with_requirement():
    with DagsterInstance.ephemeral() as instance:
        with pytest.raises(dg.DagsterUnmetExecutorRequirementsError):
            dg.execute_job(
                dg.reconstructable(requirement_executor_job),
                instance,
                raise_on_error=True,
                run_config={"execution": {"config": {"value": "secret testing value!!"}}},
            )

    with dg.instance_for_test() as instance:
        assert dg.execute_job(
            dg.reconstructable(requirement_executor_job),
            instance,
            raise_on_error=True,
            run_config={"execution": {"config": {"value": "secret testing value!!"}}},
        ).success


def executor_dict_config_configured_job():
    @executor(
        name="test_executor",
        config_schema={"value": str},
        requirements=[ExecutorRequirement.NON_EPHEMERAL_INSTANCE],
    )
    def test_executor(init_context):
        from dagster._core.executor.in_process import InProcessExecutor

        assert init_context.executor_config["value"] == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=RetryMode.from_config({"enabled": {}}),  # pyright: ignore[reportArgumentType]
            marker_to_close=None,
        )

    test_executor_configured = test_executor.configured(
        {"value": "secret testing value!!"}, "configured_test_executor"
    )

    assert test_executor_configured.get_requirements(None) == test_executor.get_requirements(None)  # pyright: ignore[reportArgumentType]

    return get_job_for_executor(test_executor_configured)


def configured_executor_job():
    @executor(
        name="test_executor",
        config_schema={"value": str},
        requirements=[ExecutorRequirement.NON_EPHEMERAL_INSTANCE],
    )
    def test_executor(init_context):
        from dagster._core.executor.in_process import InProcessExecutor

        assert init_context.executor_config["value"] == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=RetryMode.from_config({"enabled": {}}),  # pyright: ignore[reportArgumentType]
            marker_to_close=None,
        )

    test_executor_configured = test_executor.configured(
        {"value": "secret testing value!!"}, "configured_test_executor"
    )
    assert test_executor_configured.get_requirements(None) == test_executor.get_requirements(None)  # pyright: ignore[reportArgumentType]

    return get_job_for_executor(test_executor_configured)


def test_in_process_executor_dict_config_configured():
    with dg.instance_for_test() as instance:
        assert dg.execute_job(
            dg.reconstructable(configured_executor_job), instance=instance
        ).success


@dg.op
def emit_one(_):
    return 1


@dg.job(executor_def=multiprocess_executor.configured({"max_concurrent": 1}))
def multiproc_test():
    emit_one()


def test_multiproc():
    with dg.instance_for_test() as instance:
        result = dg.execute_job(
            dg.reconstructable(multiproc_test),
            run_config={
                "resources": {
                    "io_manager": {
                        "config": {"base_dir": path.join(instance.root_directory, "storage")}
                    }
                },
            },
            instance=instance,
        )
        assert result.success


@executor(config_schema=str)
def needs_config(_):
    from dagster._core.executor.in_process import InProcessExecutor

    return InProcessExecutor(
        retries=RetryMode.from_config({"enabled": {}}),  # pyright: ignore[reportArgumentType]
        marker_to_close=None,
    )


@dg.job(executor_def=needs_config)
def one_but_needs_config():
    pass


def test_defaulting_behavior():
    with dg.instance_for_test() as instance:
        with pytest.raises(dg.DagsterInvalidConfigError):
            dg.execute_job(dg.reconstructable(one_but_needs_config), instance=instance)


@executor
def executor_failing(_):
    raise dg.DagsterInvariantViolationError()


@dg.job(executor_def=executor_failing)
def job_executor_failing():
    pass


def test_failing_executor_initialization():
    with dg.instance_for_test() as instance:
        result = dg.execute_job(
            dg.reconstructable(job_executor_failing), instance=instance, raise_on_error=False
        )
        assert not result.success
        assert result.all_events[-1].event_type == DagsterEventType.RUN_FAILURE

        # Ensure that error in executor fn is properly persisted.
        event_records = instance.all_logs(result.run_id)
        assert len(event_records) == 1
        assert event_records[0].dagster_event_type == DagsterEventType.RUN_FAILURE

        run = instance.get_run_by_id(result.run_id)
        assert run.tags[RUN_FAILURE_REASON_TAG] == RunFailureReason.JOB_INITIALIZATION_FAILURE.value  # pyright: ignore[reportOptionalMemberAccess]


def test_multiprocess_executor_default():
    executor = MultiprocessExecutor(
        max_concurrent=2,
        retries=RetryMode.DISABLED,
    )

    assert executor._max_concurrent == 2  # noqa: SLF001

    executor = MultiprocessExecutor(
        max_concurrent=0,
        retries=RetryMode.DISABLED,
    )

    assert executor._max_concurrent == multiprocessing.cpu_count()  # noqa: SLF001

    with environ({"DAGSTER_MULTIPROCESS_EXECUTOR_MAX_CONCURRENT": "12345"}):
        executor = MultiprocessExecutor(
            max_concurrent=0,
            retries=RetryMode.DISABLED,
        )

        assert executor._max_concurrent == 12345  # noqa: SLF001


def test_multiprocess_executor_config():
    tag_concurrency_limits = [{"key": "database", "value": "tiny", "limit": 2}]

    executor = _core_multiprocess_executor_creation(
        {
            "retries": {
                "disabled": {},
            },
            "max_concurrent": 2,
            "tag_concurrency_limits": tag_concurrency_limits,
        }
    )
    assert executor._retries == RetryMode.DISABLED  # noqa: SLF001
    assert executor._max_concurrent == 2  # noqa: SLF001
    assert executor._tag_concurrency_limits == tag_concurrency_limits  # noqa: SLF001
    assert executor._step_dependency_config == StepDependencyConfig.default()  # noqa: SLF001


def test_multiprocess_executor_config_none_is_sentinel() -> None:
    executor = _core_multiprocess_executor_creation(
        {
            "retries": {
                "disabled": {},
            },
            "max_concurrent": None,
        }
    )
    assert executor._max_concurrent == multiprocessing.cpu_count()  # noqa: SLF001
    assert executor._step_dependency_config == StepDependencyConfig.default()  # noqa: SLF001


def test_multiprocess_executor_config_zero_is_sentinel() -> None:
    executor = _core_multiprocess_executor_creation(
        {
            "retries": {
                "disabled": {},
            },
            "max_concurrent": 0,
        }
    )
    assert executor._max_concurrent == multiprocessing.cpu_count()  # noqa: SLF001
    assert executor._step_dependency_config == StepDependencyConfig.default()  # noqa: SLF001
