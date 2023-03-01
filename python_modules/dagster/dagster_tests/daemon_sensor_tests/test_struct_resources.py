import os
import sys
from typing import Iterator, Optional

import pendulum
import pytest
from dagster import (
    SensorEvaluationContext,
    job,
    op,
    sensor,
)
from dagster._check import ParameterCheckError
from dagster._config.structured_config import ConfigurableResource
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.sensor_definition import RunRequest
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus, TickStatus
from dagster._core.test_utils import (
    create_test_daemon_workspace_context,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import ModuleTarget
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

from .test_sensor_run import evaluate_sensors, validate_tick, wait_for_all_runs_to_start

from dagster import resource
from contextlib import contextmanager
from dagster._core.definitions.resource_output import Resource


@op
def the_op(_):
    return 1


@job
def the_job():
    the_op()


class MyResource(ConfigurableResource):
    a_str: str


@sensor(job_name="the_job", required_resource_keys={"my_resource"})
def sensor_from_context(context: SensorEvaluationContext):
    return RunRequest(context.resources.my_resource.a_str, run_config={}, tags={})


@sensor(job_name="the_job")
def sensor_from_fn_arg(context: SensorEvaluationContext, my_resource: MyResource):
    return RunRequest(my_resource.a_str, run_config={}, tags={})


is_in_cm = False


@resource
@contextmanager
def my_cm_resource(_) -> Iterator[str]:
    global is_in_cm
    is_in_cm = True
    yield "foo"
    is_in_cm = False


@sensor(job_name="the_job")
def sensor_with_cm(context: SensorEvaluationContext, my_cm_resource: Resource[str]):
    assert is_in_cm
    return RunRequest(my_cm_resource, run_config={}, tags={})


@sensor(job_name="the_job", required_resource_keys={"my_resource"})
def sensor_from_context_weird_name(not_called_context: SensorEvaluationContext):
    return RunRequest(not_called_context.resources.my_resource.a_str, run_config={}, tags={})


@sensor(job_name="the_job")
def sensor_from_fn_arg_no_context(my_resource: MyResource):
    return RunRequest(my_resource.a_str, run_config={}, tags={})


@sensor(job_name="the_job")
def sensor_context_arg_not_first_and_weird_name(
    my_resource: MyResource, not_called_context: SensorEvaluationContext
):
    assert not_called_context.resources.my_resource.a_str == my_resource.a_str

    return RunRequest(not_called_context.resources.my_resource.a_str, run_config={}, tags={})


the_repo = Definitions(
    jobs=[the_job],
    sensors=[
        sensor_from_context,
        sensor_from_fn_arg,
        sensor_with_cm,
        sensor_from_context_weird_name,
        sensor_from_fn_arg_no_context,
        sensor_context_arg_not_first_and_weird_name,
    ],
    resources={
        "my_resource": MyResource(a_str="foo"),
        "my_cm_resource": my_cm_resource,
    },
)


def create_workspace_load_target(attribute: Optional[str] = SINGLETON_REPOSITORY_NAME):
    return ModuleTarget(
        module_name="dagster_tests.daemon_sensor_tests.test_struct_resources",
        attribute=None,
        working_directory=os.path.dirname(__file__),
        location_name="test_location",
    )


@pytest.fixture(name="workspace_context_struct_resources", scope="module")
def workspace_fixture(instance_module_scoped):
    with create_test_daemon_workspace_context(
        workspace_load_target=create_workspace_load_target(),
        instance=instance_module_scoped,
    ) as workspace:
        yield workspace


@pytest.fixture(name="external_repo_struct_resources", scope="module")
def external_repo_fixture(workspace_context_struct_resources: WorkspaceProcessContext):
    repo_loc = next(
        iter(
            workspace_context_struct_resources.create_request_context()
            .get_workspace_snapshot()
            .values()
        )
    ).repository_location
    assert repo_loc
    return repo_loc.get_repository(SINGLETON_REPOSITORY_NAME)


def loadable_target_origin() -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_sensor_tests.test_struct_resources",
        working_directory=os.getcwd(),
        attribute=None,
    )


def test_cant_use_required_resource_keys_and_params_both() -> None:
    with pytest.raises(ParameterCheckError):

        @sensor(job_name="the_job", required_resource_keys={"my_other_resource"})
        def sensor_from_context_and_params(
            context: SensorEvaluationContext, my_resource: MyResource
        ):
            return RunRequest(my_resource.a_str, run_config={}, tags={})


@pytest.mark.parametrize(
    "sensor_name",
    [
        "sensor_from_context",
        "sensor_from_fn_arg",
        "sensor_with_cm",
        "sensor_from_context_weird_name",
        "sensor_from_fn_arg_no_context",
        "sensor_context_arg_not_first_and_weird_name",
    ],
)
def test_resources(
    caplog,
    instance,
    workspace_context_struct_resources,
    external_repo_struct_resources,
    sensor_name,
):
    freeze_datetime = to_timezone(
        create_pendulum_time(
            year=2019,
            month=2,
            day=27,
            hour=23,
            minute=59,
            second=59,
            tz="UTC",
        ),
        "US/Central",
    )

    with pendulum.test(freeze_datetime):
        external_sensor = external_repo_struct_resources.get_external_sensor(sensor_name)
        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 0

        evaluate_sensors(workspace_context_struct_resources, None)
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 1
        run = instance.get_runs()[0]
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1
        assert ticks[0].run_keys == ["foo"]
        validate_tick(
            ticks[0],
            external_sensor,
            freeze_datetime,
            TickStatus.SUCCESS,
            expected_run_ids=[run.run_id],
        )
