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
from dagster._core.host_representation.external import ExternalRepository
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
            return VerificationResult(VerificationStatus.SUCCESS, "asdf")
        else:
            return VerificationResult(VerificationStatus.FAILURE, "qwer")


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


def test_resources(
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

    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance.get_ref(), "success_resource"
    )
    assert result.response == VerificationResult(VerificationStatus.SUCCESS, "asdf")

    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance.get_ref(), "failure_resource"
    )
    assert result.response == VerificationResult(VerificationStatus.FAILURE, "qwer")

    result = code_location.launch_resource_verification(
        external_repo.get_external_origin(), instance.get_ref(), "exception_resource"
    )
    assert result.response == VerificationResult(
        VerificationStatus.FAILURE, "Error executing verification check"
    )
    assert result.serializable_error_info
