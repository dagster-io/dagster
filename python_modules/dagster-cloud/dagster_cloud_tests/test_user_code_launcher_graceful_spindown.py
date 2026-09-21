# ruff: noqa: SLF001

import datetime
import time
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from dagster._core.test_utils import environ
from dagster_cloud import DagsterCloudAgentInstance
from dagster_cloud.workspace.user_code_launcher import UserCodeLauncherEntry
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
    CLEANUP_SERVER_GRACE_PERIOD_SECONDS,
)
from dagster_cloud_cli.core.workspace import CodeLocationDeployData
from freezegun import freeze_time

from dagster_cloud_tests.test_user_code_launcher import UserCodeTestLauncher

if TYPE_CHECKING:
    from dagster_cloud.workspace.user_code_launcher.user_code_launcher import DeploymentAndLocation


class GracefulUserCodeTestLauncher(UserCodeTestLauncher):
    @property
    def supports_get_current_runs_for_server_handle(self) -> bool:
        return True

    def run_launcher(self):
        raise NotImplementedError()

    @property
    def _reconcile_interval(self):
        return 1


@pytest.fixture
def patched_get_current_runs():
    with mock.patch.object(
        GracefulUserCodeTestLauncher, "get_current_runs_for_server_handle"
    ) as method:
        method.return_value = []
        yield method


@pytest.fixture
def patched_list_server_handles():
    with mock.patch.object(GracefulUserCodeTestLauncher, "_list_server_handles") as method:
        method.return_value = []
        yield method


@pytest.fixture
def user_code_launcher(patched_get_current_runs, patched_list_server_handles, agent_instance):
    with GracefulUserCodeTestLauncher() as user_code_launcher:
        user_code_launcher.register_instance(agent_instance)
        yield user_code_launcher


def test_graceful_multiple_agents_grpc_spindown(agent_instance: DagsterCloudAgentInstance):
    with GracefulUserCodeTestLauncher() as user_code_launcher:
        with environ({"DAGSTER_CLOUD_CLEANUP_SERVER_CHECK_INTERVAL": "0"}):
            active_agent_ids = {"different-agent-id", agent_instance.instance_uuid}
            user_code_launcher._mocked_active_agent_ids = active_agent_ids
            user_code_launcher.register_instance(agent_instance)
            user_code_launcher.start(run_reconcile_thread=False)
            now = time.time()
            one_hour_ago = now - CLEANUP_SERVER_GRACE_PERIOD_SECONDS - 1

            server_one = UserCodeLauncherEntry(
                CodeLocationDeployData("test_image:tag1", python_file="foo.py"),
                now,
            )
            server_two = UserCodeLauncherEntry(
                CodeLocationDeployData("test_image:tag2", python_file="foo.py"), now
            )
            server_three = UserCodeLauncherEntry(
                CodeLocationDeployData("test_image:tag3", python_file="foo.py"), now
            )
            server_four = UserCodeLauncherEntry(
                CodeLocationDeployData("test_image:tag4", python_file="foo.py"), now
            )

            with freeze_time(
                datetime.datetime.fromtimestamp(one_hour_ago, tz=datetime.timezone.utc)
            ):
                entry_map: dict[DeploymentAndLocation, UserCodeLauncherEntry] = {
                    ("dep1", "location1"): server_one,
                    ("dep2", "location2"): server_two,
                    ("dep3", "location3"): server_three,
                }

                user_code_launcher.update_grpc_metadata(
                    entry_map,
                    control_plane_error_locations=set(),
                    control_plane_outdated_locations=set(),
                )
                user_code_launcher.get_grpc_server_heartbeats()
                user_code_launcher.reconcile()
                user_code_launcher.get_grpc_server_heartbeats()

                assert len(user_code_launcher._agent_ids.keys()) == 3
                # Since all servers were created by this agent instance, both should be able to clean up.
                for key in user_code_launcher._agent_ids.keys():
                    assert user_code_launcher._can_cleanup_server(
                        key, active_agent_ids, include_own_servers=True
                    )

            with freeze_time(datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc)):
                entry_map[("dep4", "location4")] = server_four

                user_code_launcher.update_grpc_metadata(
                    entry_map,
                    control_plane_error_locations=set(),
                    control_plane_outdated_locations=set(),
                )
                user_code_launcher.get_grpc_server_heartbeats()
                user_code_launcher.reconcile()
                user_code_launcher.get_grpc_server_heartbeats()

                assert len(user_code_launcher._agent_ids.keys()) == 4
                # Since all servers were created by this agent instance, both should be able to clean up.
                for key in user_code_launcher._agent_ids.keys():
                    assert user_code_launcher._can_cleanup_server(
                        key, active_agent_ids, include_own_servers=True
                    )

                handle_active_agent = [
                    key
                    for key in user_code_launcher._agent_ids.keys()
                    if key.startswith("location1-dep1")
                ].pop()
                handle_inactive_agent_not_recent = [
                    key
                    for key in user_code_launcher._agent_ids.keys()
                    if key.startswith("location2-dep2")
                ].pop()

                handle_inactive_agent_recent = [
                    key
                    for key in user_code_launcher._agent_ids.keys()
                    if key.startswith("location4-dep4")
                ].pop()

                # Induce a state where one of the grpc servers was created by a different agent which is active.
                user_code_launcher._agent_ids[handle_active_agent] = "different-agent-id"

                assert not user_code_launcher._can_cleanup_server(
                    handle_active_agent, active_agent_ids, include_own_servers=True
                )

                # Induce a state where one of the grpc servers was created by a different agent which is inactive.
                user_code_launcher._agent_ids[handle_inactive_agent_not_recent] = (
                    "inactive-agent-id"
                )
                user_code_launcher._agent_ids[handle_inactive_agent_recent] = "inactive-agent-id"

                # recent ones still cannot be cleaned up
                assert not user_code_launcher._can_cleanup_server(
                    handle_inactive_agent_recent, active_agent_ids, include_own_servers=True
                )

                # non-recent ones can
                assert user_code_launcher._can_cleanup_server(
                    handle_inactive_agent_not_recent, active_agent_ids, include_own_servers=True
                )

                # Perform cleanup of grpc servers
                user_code_launcher._graceful_cleanup_servers(include_own_servers=True)
                remaining_handles = set()
                for handles in user_code_launcher._servers.values():
                    for handle in handles:
                        remaining_handles.add(handle)
                # Ensure that the handle created by this agent, and the handle created by
                # an inactive agent were both cleaned up.
                assert remaining_handles == {handle_active_agent, handle_inactive_agent_recent}


def test_mocks(user_code_launcher, patched_list_server_handles, patched_get_current_runs):
    patched_list_server_handles.return_value = [123]
    patched_get_current_runs.return_value = ["foo"]

    assert user_code_launcher._list_server_handles() == [123]
    assert user_code_launcher.get_current_runs_for_server_handle(123) == ["foo"]


def test_empty(user_code_launcher):
    user_code_launcher.start()
    user_code_launcher.wait_for_reconcile()
    with user_code_launcher._grpc_servers_lock:
        assert user_code_launcher._pending_delete_grpc_server_handles == set()


def test_cleans_up_no_active_runs(
    user_code_launcher, patched_list_server_handles, patched_get_current_runs
):
    patched_list_server_handles.return_value = [123]
    assert user_code_launcher.get_current_runs_for_server_handle(123) == []

    user_code_launcher.start()
    user_code_launcher.wait_for_reconcile()
    with user_code_launcher._grpc_servers_lock:
        assert user_code_launcher._pending_delete_grpc_server_handles == set()


def test_leaves_active_runs(
    user_code_launcher, patched_list_server_handles, patched_get_current_runs
):
    patched_list_server_handles.return_value = [123]
    patched_get_current_runs.return_value = ["f00"]

    user_code_launcher.start()
    user_code_launcher.wait_for_reconcile()
    with user_code_launcher._grpc_servers_lock:
        assert user_code_launcher._pending_delete_grpc_server_handles == {123}
    assert user_code_launcher.get_active_grpc_server_handles() == [123]

    patched_get_current_runs.return_value = []

    user_code_launcher.wait_for_reconcile()
    with user_code_launcher._grpc_servers_lock:
        assert user_code_launcher._pending_delete_grpc_server_handles == set()

    assert user_code_launcher.get_active_grpc_server_handles() == []
