import os
import sys
from typing import Any, Optional

import pytest
from dagster import (
    ConfigurableResource,
    ConfigVerifiable,
    DagsterInstance,
    Definitions,
    VerificationResult,
    VerificationStatus,
    job,
    op,
)
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.origin import (
    ExternalRepositoryOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.test_utils import (
    create_test_daemon_workspace_context,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import IWorkspaceProcessContext, WorkspaceProcessContext
from dagster._core.workspace.load_target import ModuleTarget


@pytest.fixture(name="instance_session_scoped", scope="session")
def instance_session_scoped_fixture() -> Any:
    with instance_for_test(
        overrides={
            "run_launcher": {"module": "dagster._core.test_utils", "class": "MockedRunLauncher"}
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture(instance_session_scoped) -> Any:
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_session_scoped) -> Any:
    instance_session_scoped.wipe()
    instance_session_scoped.wipe_all_schedules()
    yield instance_session_scoped


def create_workspace_load_target(attribute: Optional[str] = SINGLETON_REPOSITORY_NAME):
    return ModuleTarget(
        module_name="dagster_tests.core_tests.resource_tests.verifiable_resources.test_grpc",
        attribute=None,
        working_directory=os.path.dirname(__file__),
        location_name="test_location",
    )


@pytest.fixture(name="workspace_context", scope="module")
def workspace_fixture(instance_module_scoped) -> Any:
    with create_test_daemon_workspace_context(
        workspace_load_target=create_workspace_load_target(),
        instance=instance_module_scoped,
    ) as workspace:
        yield workspace


@pytest.fixture(name="external_repo", scope="module")
def external_repo_fixture(workspace_context: WorkspaceProcessContext):
    repo_loc = next(
        iter(workspace_context.create_request_context().get_workspace_snapshot().values())
    ).code_location
    assert repo_loc
    return repo_loc.get_repository(SINGLETON_REPOSITORY_NAME)


def loadable_target_origin() -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.core_tests.resource_tests.verifiable_resources.test_grpc",
        working_directory=os.getcwd(),
        attribute=None,
    )


@op
def the_op(_) -> Any:
    return 1


@job
def the_job() -> Any:
    the_op()


class MyVerifiableResource(ConfigurableResource, ConfigVerifiable):
    a_str: str

    def verify_config(self) -> VerificationResult:
        if self.a_str == "foo":
            return VerificationResult.success("asdf")
        else:
            return VerificationResult.failure("qwer")


class MyUnverifiableResource(ConfigurableResource, ConfigVerifiable):
    def verify_config(self) -> VerificationResult:
        raise Exception("failure")


the_repo = Definitions(
    jobs=[the_job],
    resources={
        "success_resource": MyVerifiableResource(a_str="foo"),
        "failure_resource": MyVerifiableResource(a_str="bar"),
        "exception_resource": MyUnverifiableResource(),
    },
)


def test_base_resource(
    caplog,
    instance: DagsterInstance,
    workspace_context: IWorkspaceProcessContext,
    external_repo: ExternalRepository,
) -> None:
    instance = workspace_context.instance

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace_context.create_request_context()
        .get_workspace_snapshot()
        .values()
    }

    location_entry = list(workspace_snapshot.values())[0]
    code_location = location_entry.code_location
    assert code_location

    assert (
        instance.get_ticks(
            origin_id=external_repo.get_external_origin_id(), selector_id="success_resource"
        )
        == []
    )
    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance, "success_resource"
    )
    assert result.response == VerificationResult.success("asdf")
    ticks = instance.get_ticks(
        origin_id=external_repo.get_external_origin_id(), selector_id="success_resource"
    )
    assert len(ticks) == 1
    assert ticks[0].status == TickStatus.SUCCESS
    assert ticks[0].cursor == "asdf"
    assert ticks[0].instigator_type == InstigatorType.VERIFICATION

    # Try another success run
    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance, "success_resource"
    )
    assert result.response == VerificationResult.success("asdf")
    ticks = instance.get_ticks(
        origin_id=external_repo.get_external_origin_id(), selector_id="success_resource"
    )
    assert len(ticks) == 2

    # A failed (non-exception) verification should still create a successful run
    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance, "failure_resource"
    )
    assert result.response == VerificationResult.failure("qwer")
    ticks = instance.get_ticks(
        origin_id=external_repo.get_external_origin_id(), selector_id="failure_resource"
    )
    assert len(ticks) == 1
    assert ticks[0].status == TickStatus.SKIPPED
    assert ticks[0].cursor == "qwer"
    assert ticks[0].instigator_type == InstigatorType.VERIFICATION

    # When an exception is raised in the verification, the run should fail
    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance, "exception_resource"
    )
    assert result.response == VerificationResult(
        VerificationStatus.FAILURE, "Error executing verification check"
    )
    assert result.serializable_error_info
    ticks = instance.get_ticks(
        origin_id=external_repo.get_external_origin_id(), selector_id="exception_resource"
    )
    assert len(ticks) == 1
    assert ticks[0].is_failure
    assert ticks[0].instigator_type == InstigatorType.VERIFICATION


def test_resource_not_found(
    caplog,
    instance: DagsterInstance,
    workspace_context: IWorkspaceProcessContext,
    external_repo: ExternalRepository,
) -> None:
    instance = workspace_context.instance

    workspace_snapshot = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace_context.create_request_context()
        .get_workspace_snapshot()
        .values()
    }

    location_entry = list(workspace_snapshot.values())[0]
    code_location = location_entry.code_location
    assert code_location

    assert instance.get_runs() == []

    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance, "non_existent_resource"
    )

    assert result.response.status == VerificationStatus.FAILURE
    assert (
        result.response.message
        and "Resource non_existent_resource not found" in result.response.message
    )


def test_in_process_code_location() -> None:
    with instance_for_test() as instance:
        external_repo_origin = ExternalRepositoryOrigin(
            InProcessCodeLocationOrigin(loadable_target_origin()),
            SINGLETON_REPOSITORY_NAME,
        )

        result = external_repo_origin.code_location_origin.create_location().launch_resource_verification(
            origin=external_repo_origin,
            instance=instance,
            resource_name="success_resource",
        )
        assert result.response == VerificationResult.success("asdf")

        result = external_repo_origin.code_location_origin.create_location().launch_resource_verification(
            origin=external_repo_origin,
            instance=instance,
            resource_name="failure_resource",
        )
        assert result.response == VerificationResult.failure("qwer")
