import os
import sys
from typing import Iterator, Optional, cast

import pytest
from dagster import DagsterInstance
from dagster._core.remote_representation import (
    CodeLocation,
    InProcessCodeLocationOrigin,
    RemoteRepository,
)
from dagster._core.remote_representation.origin import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext


@pytest.fixture(name="instance_module_scoped", scope="module")
def instance_module_scoped_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            }
        }
    ) as instance:
        yield instance


@pytest.fixture(name="instance", scope="function")
def instance_fixture(instance_module_scoped) -> Iterator[DagsterInstance]:
    instance_module_scoped.wipe()
    instance_module_scoped.wipe_all_schedules()
    yield instance_module_scoped


def workspace_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        InProcessCodeLocationOrigin(
            loadable_target_origin=loadable_target_origin(attribute=attribute),
            location_name="test_location",
        )
    )


@pytest.fixture(name="workspace_context", scope="module")
def workspace_fixture(instance_module_scoped) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=workspace_load_target(), instance=instance_module_scoped
    ) as workspace_context:
        yield workspace_context


@pytest.fixture(name="external_repo", scope="module")
def external_repo_fixture(
    workspace_context: WorkspaceProcessContext,
) -> Iterator[RemoteRepository]:
    yield cast(
        CodeLocation,
        next(
            iter(workspace_context.create_request_context().get_code_location_entries().values())
        ).code_location,
    ).get_repository("the_repo")


def loadable_target_origin(attribute: Optional[str] = None) -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_tests.test_backfill",
        working_directory=os.getcwd(),
        attribute=attribute,
    )


def unloadable_target_origin(attribute: Optional[str] = None) -> LoadableTargetOrigin:
    return LoadableTargetOrigin(
        executable_path=sys.executable,
        module_name="dagster_tests.daemon_tests.test_locations.unloadable_location",
        working_directory=os.getcwd(),
        attribute=attribute,
    )


def invalid_workspace_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        InProcessCodeLocationOrigin(
            loadable_target_origin=unloadable_target_origin(attribute=attribute),
            location_name="unloadable",
        )
    )


@pytest.fixture(name="unloadable_location_workspace_context", scope="module")
def unloadable_location_fixture(instance_module_scoped) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=invalid_workspace_load_target(), instance=instance_module_scoped
    ) as workspace_context:
        yield workspace_context


def partitions_def_changes_workspace_1_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        InProcessCodeLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name="dagster_tests.daemon_tests.test_locations.partitions_defs_changes_locations.location_1",
                working_directory=os.getcwd(),
                attribute=attribute,
            ),
            location_name="partitions_def_changes_1",
        )
    )


@pytest.fixture(name="partitions_defs_changes_location_1_workspace_context", scope="module")
def partitions_defs_changes_location_1_fixture(
    instance_module_scoped,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=partitions_def_changes_workspace_1_load_target(),
        instance=instance_module_scoped,
    ) as workspace_context:
        yield workspace_context


def partitions_def_changes_workspace_2_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        InProcessCodeLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name="dagster_tests.daemon_tests.test_locations.partitions_defs_changes_locations.location_2",
                working_directory=os.getcwd(),
                attribute=attribute,
            ),
            location_name="partitions_def_changes_1",
        )
    )


@pytest.fixture(name="partitions_defs_changes_location_2_workspace_context", scope="module")
def partitions_defs_changes_location_2_fixture(
    instance_module_scoped,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=partitions_def_changes_workspace_2_load_target(),
        instance=instance_module_scoped,
    ) as workspace_context:
        yield workspace_context


def base_job_name_changes_workspace_1_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        ManagedGrpcPythonEnvCodeLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name="dagster_tests.daemon_tests.test_locations.base_job_name_changes_locations.location_1",
                working_directory=os.getcwd(),
                attribute=attribute,
            ),
            location_name="base_job_name_changes",
        )
    )


@pytest.fixture(name="base_job_name_changes_location_1_workspace_context", scope="module")
def base_job_name_changes_location_1_fixture(
    instance_module_scoped,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=base_job_name_changes_workspace_1_load_target(),
        instance=instance_module_scoped,
    ) as workspace_context:
        yield workspace_context


def base_job_name_changes_workspace_2_load_target(attribute=None):
    return InProcessTestWorkspaceLoadTarget(
        ManagedGrpcPythonEnvCodeLocationOrigin(
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name="dagster_tests.daemon_tests.test_locations.base_job_name_changes_locations.location_2",
                working_directory=os.getcwd(),
                attribute=attribute,
            ),
            location_name="base_job_name_changes",
        )
    )


@pytest.fixture(name="base_job_name_changes_location_2_workspace_context", scope="module")
def base_job_name_changes_location_2_fixture(
    instance_module_scoped,
) -> Iterator[WorkspaceProcessContext]:
    with create_test_daemon_workspace_context(
        workspace_load_target=base_job_name_changes_workspace_2_load_target(),
        instance=instance_module_scoped,
    ) as workspace_context:
        yield workspace_context
