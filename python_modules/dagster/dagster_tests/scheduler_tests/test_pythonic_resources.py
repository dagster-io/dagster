import os
import sys
from typing import Optional, Sequence

import pytest
from dagster import (
    DagsterInstance,
    IAttachDifferentObjectToOpContext,
    ScheduleEvaluationContext,
    job,
    op,
    resource,
    schedule,
)
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.definitions.schedule_definition import RunRequest
from dagster._core.scheduler.instigation import InstigatorTick, TickStatus
from dagster._core.test_utils import create_test_daemon_workspace_context, freeze_time
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import ModuleTarget
from dagster._time import create_datetime, get_current_datetime, get_timezone
from dagster._vendored.dateutil.relativedelta import relativedelta

from dagster_tests.scheduler_tests.test_scheduler_run import (
    evaluate_schedules,
    validate_tick,
    wait_for_all_runs_to_start,
)


@op
def the_op(_):
    return 1


@job
def the_job():
    the_op()


class MyResource(ConfigurableResource):
    a_str: str


class MyResourceAttachDifferentObject(ConfigurableResource, IAttachDifferentObjectToOpContext):
    a_str: str

    def get_object_to_set_on_execution_context(self) -> str:
        return self.a_str


@schedule(job_name="the_job", cron_schedule="* * * * *", required_resource_keys={"my_resource"})
def schedule_from_context(context: ScheduleEvaluationContext):
    return RunRequest(context.resources.my_resource.a_str, run_config={}, tags={})


@schedule(job_name="the_job", cron_schedule="* * * * *")
def schedule_from_arg(my_resource: MyResource):
    return RunRequest(my_resource.a_str, run_config={}, tags={})


@schedule(job_name="the_job", cron_schedule="* * * * *")
def schedule_from_weird_name(
    my_resource: MyResource, not_called_context: ScheduleEvaluationContext
):
    assert not_called_context.resources.my_resource.a_str == my_resource.a_str

    return RunRequest(my_resource.a_str, run_config={}, tags={})


@schedule(job_name="the_job", cron_schedule="* * * * *")
def schedule_with_resource_from_context(
    context: ScheduleEvaluationContext, my_resource_attach: MyResourceAttachDifferentObject
):
    assert context.resources.my_resource_attach == my_resource_attach.a_str

    return RunRequest(my_resource_attach.a_str, run_config={}, tags={})


@resource
def the_inner() -> str:
    return "oo"


@resource(required_resource_keys={"the_inner"})
def the_outer(init_context) -> str:
    return "f" + init_context.resources.the_inner


@schedule(
    job_name="the_job",
    required_resource_keys={"the_outer"},
    cron_schedule="* * * * *",
)
def schedule_resource_deps(context):
    return RunRequest("foo", run_config={}, tags={})


the_repo = Definitions(
    jobs=[the_job],
    schedules=[
        schedule_from_context,
        schedule_from_arg,
        schedule_from_weird_name,
        schedule_with_resource_from_context,
        schedule_resource_deps,
    ],
    resources={
        "my_resource": MyResource(a_str="foo"),
        "my_resource_attach": MyResourceAttachDifferentObject(a_str="foo"),
        "the_inner": the_inner,
        "the_outer": the_outer,
    },
)


def create_workspace_load_target(attribute: Optional[str] = SINGLETON_REPOSITORY_NAME):
    return ModuleTarget(
        module_name="dagster_tests.scheduler_tests.test_pythonic_resources",
        attribute=None,
        working_directory=os.path.join(os.path.dirname(__file__), "..", ".."),
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
    ).code_location
    assert repo_loc
    return repo_loc.get_repository(SINGLETON_REPOSITORY_NAME)


def loadable_target_origin() -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_schedule_tests.test_pythonic_resources",
        working_directory=os.getcwd(),
        attribute=None,
    )


@pytest.mark.parametrize(
    "schedule_name",
    [
        "schedule_from_context",
        "schedule_from_arg",
        "schedule_from_weird_name",
        "schedule_with_resource_from_context",
        "schedule_resource_deps",
    ],
)
def test_resources(
    caplog,
    instance: DagsterInstance,
    workspace_context_struct_resources,
    external_repo_struct_resources,
    schedule_name,
) -> None:
    freeze_datetime = create_datetime(
        year=2019,
        month=2,
        day=27,
        hour=23,
        minute=59,
        second=59,
    ).astimezone(get_timezone("US/Central"))

    with freeze_time(freeze_datetime):
        external_schedule = external_repo_struct_resources.get_external_schedule(schedule_name)
        instance.start_schedule(external_schedule)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_schedule.get_external_origin_id(), external_schedule.selector_id
        )
        assert len(ticks) == 0
    freeze_datetime = freeze_datetime + relativedelta(seconds=30)

    with freeze_time(freeze_datetime):
        evaluate_schedules(workspace_context_struct_resources, None, get_current_datetime())
        wait_for_all_runs_to_start(instance)

        ticks: Sequence[InstigatorTick] = instance.get_ticks(
            external_schedule.get_external_origin_id(), external_schedule.selector_id
        )

        assert len(ticks) == 1

        assert instance.get_runs_count() == 1
        run = next(iter(instance.get_runs()))
        assert ticks[0].run_keys == ["foo"]

        expected_datetime = create_datetime(year=2019, month=2, day=28)
        validate_tick(
            ticks[0],
            external_schedule,
            expected_datetime,
            TickStatus.SUCCESS,
            expected_run_ids=[run.run_id],
        )
