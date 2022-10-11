from os import path

import pytest

from dagster import DagsterInstance, ExecutorRequirement
from dagster import _check as check
from dagster import execute_job, job, multiprocess_executor, op, reconstructable
from dagster._core.definitions.executor_definition import executor
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster._core.events import DagsterEventType
from dagster._core.execution.retries import RetryMode
from dagster._core.test_utils import instance_for_test


def get_job_for_executor(executor_def, execution_config=None):
    it = {}

    @op
    def a_op(_):
        it["ran"] = True

    @job(
        name="testing_job",
        executor_def=executor_def.configured(execution_config)
        if execution_config
        else executor_def,
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
            retries=RetryMode.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    return get_job_for_executor(test_executor)


def test_in_process_executor_primitive_config():
    with instance_for_test() as instance:
        with pytest.raises(check.ParameterCheckError):
            execute_job(
                reconstructable(primitive_config_executor_job),
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
            retries=RetryMode.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    return get_job_for_executor(test_executor)


def test_in_process_executor_dict_config():
    with instance_for_test() as instance:
        assert execute_job(
            reconstructable(dict_config_executor_job),
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
            retries=RetryMode.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    return get_job_for_executor(test_executor)


def test_in_process_executor_with_requirement():
    with DagsterInstance.ephemeral() as instance:
        with pytest.raises(DagsterUnmetExecutorRequirementsError):
            execute_job(
                reconstructable(requirement_executor_job),
                instance,
                raise_on_error=True,
                run_config={"execution": {"config": {"value": "secret testing value!!"}}},
            )

    with instance_for_test() as instance:
        assert execute_job(
            reconstructable(requirement_executor_job),
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
            retries=RetryMode.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    test_executor_configured = test_executor.configured(
        {"value": "secret testing value!!"}, "configured_test_executor"
    )

    assert test_executor_configured.get_requirements(None) == test_executor.get_requirements(None)

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
            retries=RetryMode.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    test_executor_configured = test_executor.configured(
        {"value": "secret testing value!!"}, "configured_test_executor"
    )
    assert test_executor_configured.get_requirements(None) == test_executor.get_requirements(None)

    return get_job_for_executor(test_executor_configured)


def test_in_process_executor_dict_config_configured():

    with instance_for_test() as instance:
        assert execute_job(reconstructable(configured_executor_job), instance=instance).success


@op
def emit_one(_):
    return 1


@job(executor_def=multiprocess_executor.configured({"max_concurrent": 1}))
def multiproc_test():
    emit_one()


def test_multiproc():

    with instance_for_test() as instance:

        result = execute_job(
            reconstructable(multiproc_test),
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
        retries=RetryMode.from_config({"enabled": {}}),
        marker_to_close=None,
    )


@job(executor_def=needs_config)
def one_but_needs_config():
    pass


def test_defaulting_behavior():

    with instance_for_test() as instance:
        with pytest.raises(DagsterInvalidConfigError):
            execute_job(reconstructable(one_but_needs_config), instance=instance)


@executor
def executor_failing(_):
    raise DagsterInvariantViolationError()


@job(executor_def=executor_failing)
def job_executor_failing():
    pass


def test_failing_executor_initialization():
    with instance_for_test() as instance:

        result = execute_job(
            reconstructable(job_executor_failing), instance=instance, raise_on_error=False
        )
        assert not result.success
        assert result.all_events[-1].event_type == DagsterEventType.RUN_FAILURE

        # Ensure that error in executor fn is properly persisted.
        event_records = instance.all_logs(result.run_id)
        assert len(event_records) == 1
        assert event_records[0].dagster_event_type == DagsterEventType.RUN_FAILURE
