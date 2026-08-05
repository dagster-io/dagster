# ruff: noqa: SLF001
import datetime
import logging
import time
from collections import defaultdict
from collections.abc import Collection, Generator
from typing import TYPE_CHECKING, Any
from unittest import mock

import dagster._check as check
import pytest
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import environ
from dagster._serdes import serialize_value
from dagster._time import datetime_from_timestamp, get_current_datetime, get_current_timestamp
from dagster._utils.error import SerializableErrorInfo
from dagster_cloud import DagsterCloudAgentInstance
from dagster_cloud.api.dagster_cloud_api import (
    DagsterCloudUploadLocationData,
    DagsterCloudUploadWorkspaceEntry,
    UserCodeDeploymentType,
)
from dagster_cloud.execution.monitoring import CloudCodeServerHeartbeat, CloudCodeServerStatus
from dagster_cloud.pex.grpc.types import PexServerHandle
from dagster_cloud.workspace.user_code_launcher import (
    DagsterCloudGrpcServer,
    DagsterCloudUserCodeLauncher,
    ServerEndpoint,
    UserCodeLauncherEntry,
)
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
    ACTUAL_ENTRIES_REFRESH_INTERVAL,
    CLEANUP_SERVER_GRACE_PERIOD_SECONDS,
    async_serialize_exceptions,
)
from dagster_cloud.workspace.user_code_launcher.utils import unique_resource_name
from dagster_cloud_cli.core.workspace import CodeLocationDeployData, PexMetadata
from dagster_shared.serdes.utils import create_snapshot_id
from freezegun import freeze_time

if TYPE_CHECKING:
    from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
        UserCodeLauncherEntryMap,
    )

ServerKey = tuple[str, str]
ServerHandle = str


class UserCodeTestLauncher(DagsterCloudUserCodeLauncher[ServerHandle]):
    def __init__(self, requires_images=True):
        self._servers: dict[ServerKey, set[ServerHandle]] = {}
        self._multipex_server_handles: dict[ServerKey, set[ServerHandle]] = {}

        self._pex_servers: dict[ServerHandle, list[PexServerHandle]] = defaultdict(list)

        self._agent_ids: dict[ServerHandle, str] = {}
        self._server_create_timestamps: dict[ServerHandle, float] = {}

        self._mocked_active_agent_ids: set[str] = set()

        self._server_create_counter = 0
        super().__init__()
        self.fail_next_add = False
        self.fail_next_add_after_server_added = set()

        self.fail_next_multipex_health_check = False

        self.fail_next_remove = False
        self.fail_graphql_writes = False
        self._requires_images = requires_images
        self._uploaded_entries = []

    def get_host_name(self, deployment_name, location_name, metadata):
        # pex_tag does not determine the hostname so we replicate that logic in this test
        metadata = metadata._replace(
            pex_metadata=PexMetadata(
                pex_tag="",
                python_version=metadata.pex_metadata.python_version
                if metadata.pex_metadata
                else None,
            )
        )
        return f"{deployment_name}_{location_name}_{create_snapshot_id(metadata)[0:6]}"

    def get_active_agent_ids(self) -> set[str]:
        return self._mocked_active_agent_ids

    @property
    def requires_images(self):
        return self._requires_images

    @property
    def servers(self) -> dict[ServerKey, set[ServerHandle]]:
        return self._servers.copy()

    @property
    def user_code_deployment_type(self) -> UserCodeDeploymentType:
        return UserCodeDeploymentType.UNKNOWN

    @property
    def multipex_server_handles(self) -> dict[ServerKey, set[ServerHandle]]:
        return self._multipex_server_handles.copy()

    @property
    def pex_servers(self) -> dict[str, list[PexServerHandle]]:
        return self._pex_servers.copy()

    def get_code_server_resource_limits(self, deployment_name, location_name):
        return {}

    def _start_new_server_spinup(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
    ) -> DagsterCloudGrpcServer:
        metadata = desired_entry.code_location_deploy_data

        if self.fail_next_add:
            self.fail_next_add = False
            raise Exception("Server add failed")

        self._server_create_counter = self._server_create_counter + 1

        container_name = unique_resource_name(
            deployment_name, location_name, length_limit=50, sanitize_fn=None
        )

        endpoint = ServerEndpoint(
            host=self.get_host_name(deployment_name, location_name, metadata),
            port=4000 + self._server_create_counter,
            socket=None,
        )

        server_key = (deployment_name, location_name)

        if metadata.pex_metadata:
            if server_key not in self._servers:
                self._multipex_server_handles[server_key] = set()

            self._multipex_server_handles[server_key].add(container_name)

        else:
            if server_key not in self._servers:
                self._servers[server_key] = set()

            self._servers[server_key].add(container_name)
            self._agent_ids[container_name] = self._instance.instance_uuid
            self._server_create_timestamps[container_name] = get_current_timestamp()

        return DagsterCloudGrpcServer(container_name, endpoint, metadata)

    def get_agent_id_for_server(self, handle: ServerHandle) -> str | None:
        return self._agent_ids.get(handle)

    def get_server_create_timestamp(self, handle: ServerHandle) -> float | None:
        return self._server_create_timestamps.get(handle)

    def _list_server_handles(self) -> list[ServerHandle]:
        all_handles = set()
        for handles in self._servers.values():
            for handle in handles:
                all_handles.add(handle)
        return list(all_handles) + list(self._pex_servers.keys())

    @async_serialize_exceptions
    async def _wait_for_new_multipex_server(
        self,
        deployment_name: str,
        location_name: str,
        server_handle: ServerHandle,
        multipex_endpoint: ServerEndpoint,
    ):
        if location_name in self.fail_next_add_after_server_added:
            self.fail_next_add_after_server_added.remove(location_name)
            raise Exception("Server add failed after creating the server")

    async def _wait_for_new_server_ready(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
        server_handle: ServerHandle,
        server_endpoint: ServerEndpoint,
    ) -> None:
        if location_name in self.fail_next_add_after_server_added:
            self.fail_next_add_after_server_added.remove(location_name)
            raise Exception("Server add failed after creating the server")

    def _create_pex_server(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
        multipex_server: DagsterCloudGrpcServer,
    ):
        self._pex_servers[multipex_server.server_handle].append(
            PexServerHandle(
                deployment_name=deployment_name,
                location_name=location_name,
                metadata_update_timestamp=int(desired_entry.update_timestamp),
            )
        )
        self._agent_ids[multipex_server.server_handle] = self._instance.instance_uuid
        self._server_create_timestamps[multipex_server.server_handle] = get_current_timestamp()

    def _get_existing_pex_servers(
        self, deployment_name: str, location_name: str
    ) -> list[PexServerHandle]:
        multipex_server = self._multipex_servers.get((deployment_name, location_name))
        if not multipex_server:
            return []

        return self._pex_servers.get(multipex_server.server_handle, []).copy()

    def _remove_pex_server_handle(  # ty: ignore[invalid-method-override], fix me!
        self,
        _deployment_name,
        _location_name,
        server_handle: ServerHandle,
        _server_endpoint: ServerEndpoint,
        pex_server_handle: PexServerHandle,
    ) -> None:
        self._pex_servers[server_handle].remove(pex_server_handle)

    async def _get_upload_location_data(
        self,
        deployment_name: str,
        location_name: str,
        server: DagsterCloudGrpcServer,
    ) -> DagsterCloudUploadLocationData:
        return DagsterCloudUploadLocationData(
            upload_repository_datas=[],
            container_image="fake_image",
            executable_path="fake_executable",
        )

    def _check_running_multipex_server(self, _multipex_server: DagsterCloudGrpcServer):  # ty: ignore[invalid-method-override], fix me!
        if self.fail_next_multipex_health_check:
            self.fail_next_multipex_health_check = False
            raise Exception("can no longer reach multipex server")

    def _get_standalone_dagster_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> Collection[str]:
        return self._servers.get((deployment_name, location_name), set()).copy()

    def _get_multipex_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> Collection[str]:
        return self._multipex_server_handles.get((deployment_name, location_name), set()).copy()

    def _remove_server_handle(self, server_handle: ServerHandle) -> None:
        if self.fail_next_remove:
            self.fail_next_remove = False
            raise Exception("Server cleanup after update failed")

        for server_handles in self._servers.values():
            if server_handle in server_handles:
                server_handles.remove(server_handle)
        for server_handles in self._multipex_server_handles.values():
            if server_handle in server_handles:
                server_handles.remove(server_handle)

        self._pex_servers.pop(server_handle, None)
        self._agent_ids.pop(server_handle, None)
        self._server_create_timestamps.pop(server_handle, None)

        time.sleep(0.5)

    def _update_workspace_entry(self, _deployment_name: str, workspace_entry, server_or_error):  # ty: ignore[invalid-method-override], fix me!
        if self.fail_graphql_writes:
            raise Exception("Update workspace entry failed")

        self._uploaded_entries.append(workspace_entry)

    def _resolve_image(self, metadata: CodeLocationDeployData) -> str | None:
        # use the pex python version if the image is missing, to simulate the behavior in serverless
        if metadata.image:
            return metadata.image
        if metadata.pex_metadata and metadata.pex_metadata.python_version:
            return "base-image-for:" + metadata.pex_metadata.python_version

        return None

    @property
    def uploaded_entries(self) -> list[DagsterCloudUploadWorkspaceEntry]:
        return self._uploaded_entries.copy()

    @property
    def uploaded_locations(self) -> list[str]:
        return [entry.location_name for entry in self._uploaded_entries]

    def wait_for_reconcile(self):
        with self._metadata_lock:
            start_count = self._reconcile_count

        # Wait for reconcile
        start_time = time.time()
        timeout = 5

        while True:
            with self._metadata_lock:
                new_count = self._reconcile_count

            if new_count > start_count:
                break

            if time.time() - start_time > timeout:
                raise Exception("Timed out waiting for reconcile")
            time.sleep(1)

    def assert_reconciliation(
        self,
        expected_entry_map: dict[tuple[str, str], UserCodeLauncherEntry],
        expected_errors: dict[tuple[Any, ...], str] | None = None,
        run_reconcile_thread: bool = True,
    ):
        if run_reconcile_thread:
            self.wait_for_reconcile()

        expected_errors = check.opt_dict_param(
            expected_errors, "expected_errors", key_type=tuple, value_type=str
        )
        expected_metadata = {
            location: entry.code_location_deploy_data
            for location, entry in expected_entry_map.items()
        }

        grpc_endpoints = self.get_grpc_endpoints()
        grpc_map = {
            key: grpc_endpoint.host
            for key, grpc_endpoint in grpc_endpoints.items()
            if not isinstance(grpc_endpoint, SerializableErrorInfo)
        }

        error_map = {
            key: grpc_endpoint
            for key, grpc_endpoint in grpc_endpoints.items()
            if isinstance(grpc_endpoint, SerializableErrorInfo)
        }

        metadata_map = {}
        for key, metadata in expected_metadata.items():
            deployment_name, location_name = key
            metadata_map[key] = self.get_host_name(deployment_name, location_name, metadata)

        assert grpc_map == metadata_map, str(error_map)

        assert expected_errors.keys() == error_map.keys()
        for error in error_map:
            assert expected_errors[error] in str(error_map[error])

    def run_launcher(self):
        raise NotImplementedError()


def _check_update(
    user_code_launcher,
    entry_map: dict[tuple[str, str], UserCodeLauncherEntry],
    expected_entry_map: dict[tuple[str, str], UserCodeLauncherEntry] | None = None,
    agent_error_map=None,
    control_plane_error_locations: set[tuple[str, str]] | None = None,
):
    expected_entry_map = expected_entry_map if expected_entry_map is not None else entry_map
    user_code_launcher.update_grpc_metadata(
        entry_map,
        control_plane_error_locations=control_plane_error_locations or set(),
        control_plane_outdated_locations=set(),
    )
    user_code_launcher.assert_reconciliation(expected_entry_map, agent_error_map)


@pytest.fixture
def user_code_launcher(
    caplog: pytest.LogCaptureFixture, agent_instance: DagsterCloudAgentInstance
) -> Generator[UserCodeTestLauncher, None, None]:
    caplog.set_level(logging.INFO)
    with UserCodeTestLauncher() as user_code_launcher:
        user_code_launcher.register_instance(agent_instance)
        yield user_code_launcher


@pytest.fixture
def user_code_launcher_no_images(
    agent_instance: DagsterCloudAgentInstance,
) -> Generator[UserCodeTestLauncher, None, None]:
    with UserCodeTestLauncher(requires_images=False) as user_code_launcher:
        user_code_launcher.register_instance(agent_instance)
        yield user_code_launcher


def test_server_cleanup_failure(
    agent_instance: DagsterCloudAgentInstance, caplog: pytest.LogCaptureFixture
):
    with UserCodeTestLauncher() as user_code_launcher:
        user_code_launcher.register_instance(agent_instance)
        user_code_launcher.start(run_reconcile_thread=False)
        now = time.time()
        server_one = UserCodeLauncherEntry(
            CodeLocationDeployData("test_image:tag1", python_file="foo.py"),
            now,
        )

        user_code_launcher.update_grpc_metadata(
            {("dep1", "location1"): server_one},
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(),
        )
        user_code_launcher.get_grpc_server_heartbeats()
        user_code_launcher.reconcile()
        user_code_launcher.get_grpc_server_heartbeats()

        user_code_launcher.fail_next_remove = True
        # Ensure that cleaning up servers doesnt cause program exit
        user_code_launcher._cleanup_servers(
            {agent_instance.instance_uuid}, include_own_servers=True
        )

        # Ensure that an error actually occurred, and we logged it.
        assert caplog.text.count("Error cleaning up server") == 1


def test_server_cleanup_parallelized(agent_instance: DagsterCloudAgentInstance):
    with UserCodeTestLauncher() as user_code_launcher:
        user_code_launcher.register_instance(agent_instance)
        user_code_launcher.start(run_reconcile_thread=False)
        now = time.time()
        server = UserCodeLauncherEntry(
            CodeLocationDeployData("test_image:tag1", python_file="foo.py"),
            now,
        )
        user_code_launcher.update_grpc_metadata(
            {(f"dep{i}", f"location{i}"): server for i in range(20)},
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(),
        )

        user_code_launcher.get_grpc_server_heartbeats()
        user_code_launcher.reconcile()
        user_code_launcher.get_grpc_server_heartbeats()

        now = time.time()
        user_code_launcher._cleanup_servers(
            {agent_instance.instance_uuid}, include_own_servers=True
        )
        assert time.time() - now < 5


def test_multiple_agents_grpc_spindown(agent_instance: DagsterCloudAgentInstance):
    with UserCodeTestLauncher() as user_code_launcher:
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

        pex_server_one = UserCodeLauncherEntry(
            CodeLocationDeployData(
                "test_image:tag1",
                python_file="foo.py",
                pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
            ),
            now,
        )
        pex_server_two = UserCodeLauncherEntry(
            CodeLocationDeployData(
                "test_image:tag2",
                python_file="foo.py",
                pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
            ),
            now,
        )
        pex_server_three = UserCodeLauncherEntry(
            CodeLocationDeployData(
                "test_image:tag3",
                python_file="foo.py",
                pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
            ),
            now,
        )
        pex_server_four = UserCodeLauncherEntry(
            CodeLocationDeployData(
                "test_image:tag4",
                python_file="foo.py",
                pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
            ),
            now,
        )

        with freeze_time(datetime.datetime.fromtimestamp(one_hour_ago, tz=datetime.timezone.utc)):
            entry_map: UserCodeLauncherEntryMap = {
                ("dep1", "location1"): server_one,
                ("dep2", "location2"): server_two,
                ("dep3", "location3"): server_three,
                ("dep1", "location5"): pex_server_one,
                ("dep2", "location6"): pex_server_two,
                ("dep3", "location7"): pex_server_three,
            }

            user_code_launcher.update_grpc_metadata(
                entry_map,
                control_plane_error_locations=set(),
                control_plane_outdated_locations=set(),
            )
            user_code_launcher.get_grpc_server_heartbeats()
            user_code_launcher.reconcile()
            user_code_launcher.get_grpc_server_heartbeats()

            assert len(user_code_launcher._agent_ids.keys()) == 6

        with freeze_time(datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc)):
            entry_map[("dep4", "location4")] = server_four
            entry_map[("dep4", "location8")] = pex_server_four

            user_code_launcher.update_grpc_metadata(
                entry_map,
                control_plane_error_locations=set(),
                control_plane_outdated_locations=set(),
            )
            user_code_launcher.get_grpc_server_heartbeats()
            user_code_launcher.reconcile()
            user_code_launcher.get_grpc_server_heartbeats()

            assert len(user_code_launcher._agent_ids.keys()) == 8
            # Since all servers were created by this agent instance, both should be able to clean up.
            for key in user_code_launcher._agent_ids.keys():
                assert user_code_launcher._can_cleanup_server(
                    key, active_agent_ids, include_own_servers=True
                )

                # even if the active_agent_ids are None due to the graphql query failing
                assert user_code_launcher._can_cleanup_server(
                    key, active_agent_ids=None, include_own_servers=True
                )

            handle_active_agent = [
                key
                for key in user_code_launcher._agent_ids.keys()
                if key.startswith("location1-dep1")
            ].pop()
            pex_handle_active_agent = [
                key
                for key in user_code_launcher._agent_ids.keys()
                if key.startswith("location5-dep1")
            ].pop()

            handle_inactive_agent_not_recent = [
                key
                for key in user_code_launcher._agent_ids.keys()
                if key.startswith("location2-dep2")
            ].pop()
            pex_handle_inactive_agent_not_recent = [
                key
                for key in user_code_launcher._agent_ids.keys()
                if key.startswith("location6-dep2")
            ].pop()

            handle_inactive_agent_recent = [
                key
                for key in user_code_launcher._agent_ids.keys()
                if key.startswith("location4-dep4")
            ].pop()
            pex_handle_inactive_agent_recent = [
                key
                for key in user_code_launcher._agent_ids.keys()
                if key.startswith("location8-dep4")
            ].pop()

            # Induce a state where one of the grpc servers was created by a different agent which is active.
            user_code_launcher._agent_ids[handle_active_agent] = "different-agent-id"
            user_code_launcher._agent_ids[pex_handle_active_agent] = "different-agent-id"

            assert not user_code_launcher._can_cleanup_server(
                handle_active_agent, active_agent_ids, include_own_servers=True
            )
            assert not user_code_launcher._can_cleanup_server(
                pex_handle_active_agent,
                active_agent_ids,
                include_own_servers=True,
            )

            # Induce a state where one of the grpc servers was created by a different agent which is inactive.
            user_code_launcher._agent_ids[handle_inactive_agent_recent] = "inactive-agent-id"
            user_code_launcher._agent_ids[pex_handle_inactive_agent_recent] = "inactive-agent-id"

            # recent ones still cannot be cleaned up
            assert not user_code_launcher._can_cleanup_server(
                handle_inactive_agent_recent, active_agent_ids, include_own_servers=True
            )
            assert not user_code_launcher._can_cleanup_server(
                pex_handle_inactive_agent_recent, active_agent_ids, include_own_servers=True
            )

            # non-recent ones can
            user_code_launcher._agent_ids[handle_inactive_agent_not_recent] = "inactive-agent-id"
            user_code_launcher._agent_ids[pex_handle_inactive_agent_not_recent] = (
                "inactive-agent-id"
            )

            assert user_code_launcher._can_cleanup_server(
                handle_inactive_agent_not_recent, active_agent_ids, include_own_servers=True
            )
            assert user_code_launcher._can_cleanup_server(
                pex_handle_inactive_agent_not_recent, active_agent_ids, include_own_servers=True
            )

            # If the active agent IDs are None (due to the graphql query failing) they can no longer be cleaned up
            assert not user_code_launcher._can_cleanup_server(
                handle_inactive_agent_not_recent, active_agent_ids=None, include_own_servers=True
            )
            assert not user_code_launcher._can_cleanup_server(
                pex_handle_inactive_agent_not_recent,
                active_agent_ids=None,
                include_own_servers=True,
            )

            # Perform cleanup of grpc servers
            user_code_launcher._graceful_cleanup_servers(include_own_servers=True)
            remaining_handles = set()
            for handles in user_code_launcher._servers.values():
                for handle in handles:
                    remaining_handles.add(handle)
            for handle in user_code_launcher._pex_servers.keys():
                remaining_handles.add(handle)
            # Ensure that the handle created by this agent, and the handle created by
            # an inactive agent were both cleaned up.
            assert remaining_handles == {
                handle_active_agent,
                pex_handle_active_agent,
                handle_inactive_agent_recent,
                pex_handle_inactive_agent_recent,
            }


def test_reconcile_loop_does_cleanup(agent_instance: DagsterCloudAgentInstance):
    with UserCodeTestLauncher() as user_code_launcher:
        active_agent_ids = {"different-agent-id", agent_instance.instance_uuid}
        user_code_launcher._mocked_active_agent_ids = active_agent_ids
        user_code_launcher.register_instance(agent_instance)
        user_code_launcher.start(run_reconcile_thread=False)
        now = time.time()
        with freeze_time(datetime_from_timestamp(now)):
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
            entry_map: UserCodeLauncherEntryMap = {
                ("dep1", "location1"): server_one,
                ("dep2", "location2"): server_two,
                ("dep3", "location3"): server_three,
            }
            user_code_launcher.update_grpc_metadata(
                entry_map,
                control_plane_error_locations=set(),
                control_plane_outdated_locations=set(),
            )
            user_code_launcher.reconcile()

            assert len(user_code_launcher._list_server_handles()) == 3

            handles = list(user_code_launcher._agent_ids.keys())
            assert len(handles) == 3
            # Induce a state where two of the grpc servers was created by a different agent which is inactive.
            for i in range(2):
                user_code_launcher._agent_ids[handles[i]] = "inactive-agent-id"

            assert len(user_code_launcher._servers) == 3
            user_code_launcher.reconcile()

            # Still 3 until the right amount of time passes
            assert len(user_code_launcher._list_server_handles()) == 3

        with freeze_time(
            datetime_from_timestamp(
                now
                + max(
                    user_code_launcher._cleanup_server_check_interval(),
                    CLEANUP_SERVER_GRACE_PERIOD_SECONDS,
                )
                + 1
            )
        ):
            user_code_launcher.reconcile()
            # The two servers have now been cleaned up
            assert len(user_code_launcher._list_server_handles()) == 1


def test_recovery_after_failed_redeploy(user_code_launcher: UserCodeTestLauncher):
    """Test the self-healing recovery mechanism for failed non-upload redeploys.

    Scenario:
    1. Agent deploys a code server successfully.
    2. _refresh_actual_entries detects the server moved to an error state (e.g.
       list_repositories returns an error) and triggers a recovery redeploy.
    3. The redeploy fails transiently - agent is now stuck because actual == desired
       but _grpc_servers has an error.
    4. On the next workspace query, the server reports no error (hasLoadError=False).
       The recovery mechanism detects the mismatch and triggers another redeploy.
    5. The redeploy succeeds and the location is healthy again.
    """
    user_code_launcher.start(run_reconcile_thread=False)

    now = get_current_datetime()
    now_timestamp = now.timestamp()

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now_timestamp
    )
    metadata_map: UserCodeLauncherEntryMap = {("dep1", "location1"): server_one}

    # Step 1: Deploy successfully
    with freeze_time(now):
        user_code_launcher.update_grpc_metadata(
            metadata_map,
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(),
        )
        user_code_launcher.reconcile()
        user_code_launcher.assert_reconciliation(
            expected_entry_map=metadata_map, run_reconcile_thread=False
        )
        initial_servers = user_code_launcher.get_grpc_endpoints()
        assert isinstance(initial_servers[("dep1", "location1")], ServerEndpoint)

    # Step 2: _refresh_actual_entries detects server moved to error state.
    # The recovery redeploy FAILS because of a transient error.
    frozen_datetime = now + datetime.timedelta(seconds=ACTUAL_ENTRIES_REFRESH_INTERVAL + 1)
    with freeze_time(frozen_datetime):
        # Make list_repositories return an error so _refresh_actual_entries triggers recovery
        mock_method = mock.patch.object(
            initial_servers[("dep1", "location1")],
            "create_client",
            return_value=mock.MagicMock(
                list_repositories=lambda: serialize_value(
                    SerializableErrorInfo(
                        message="test error", stack=[], cls_name="TestError", cause=None
                    )
                )
            ),
        )
        mock_method.start()

        # Make the redeploy fail
        user_code_launcher.fail_next_add = True

        # The control plane doesn't know about this error — the agent's local
        # health check (list_repositories) is what detects it.
        user_code_launcher.update_grpc_metadata(
            metadata_map,
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(),
        )
        user_code_launcher.reconcile()

        mock_method.stop()

        # Step 3: Agent is stuck - actual == desired but _grpc_servers has an error
        servers = user_code_launcher.get_grpc_endpoints()
        assert isinstance(servers[("dep1", "location1")], SerializableErrorInfo)
        assert ("dep1", "location1") in user_code_launcher._actual_entries

    # Step 4: Next workspace query - server reports no error (hasLoadError=False).
    # Recovery mechanism runs inside _refresh_actual_entries every 30s.
    frozen_datetime2 = frozen_datetime + datetime.timedelta(
        seconds=ACTUAL_ENTRIES_REFRESH_INTERVAL + 1
    )
    with freeze_time(frozen_datetime2):
        user_code_launcher.update_grpc_metadata(
            metadata_map,
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(),
        )
        user_code_launcher.reconcile()

        # Step 5: Location should be healthy again
        recovered_servers = user_code_launcher.get_grpc_endpoints()
        assert isinstance(recovered_servers[("dep1", "location1")], ServerEndpoint)


def test_redeploy_when_server_moves_to_error_state(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start(run_reconcile_thread=False)

    now = get_current_datetime()
    now_timestamp = now.timestamp()

    user_code_launcher.fail_next_add_after_server_added = {"location1"}

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now_timestamp
    )
    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="bar.py"), now_timestamp
    )
    server_three = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag3", python_file="baz.py"), now_timestamp
    )
    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep1", "location2"): server_two,
        ("dep1", "location3"): server_three,
    }
    with freeze_time(now):
        # all three locations are 'outdated' (in the process of being updated),
        # but this agent is not being asked to upload the results for any of them
        user_code_launcher.update_grpc_metadata(
            metadata_map,
            control_plane_error_locations=set(),
            control_plane_outdated_locations={
                ("dep1", "location1"),
                ("dep1", "location2"),
                ("dep1", "location3"),
            },
        )
        user_code_launcher.reconcile()
        user_code_launcher.assert_reconciliation(
            expected_entry_map={
                ("dep1", "location2"): server_two,
                ("dep1", "location3"): server_three,
            },
            expected_errors={("dep1", "location1"): "Server add failed after creating the server"},
            run_reconcile_thread=False,
        )

        initial_reconciled_servers = user_code_launcher.get_grpc_endpoints()

        assert isinstance(initial_reconciled_servers[("dep1", "location1")], SerializableErrorInfo)
        assert isinstance(initial_reconciled_servers[("dep1", "location2")], ServerEndpoint)
        assert isinstance(initial_reconciled_servers[("dep1", "location3")], ServerEndpoint)

        initial_actual_entries = user_code_launcher._actual_entries

    frozen_datetime = now + datetime.timedelta(seconds=ACTUAL_ENTRIES_REFRESH_INTERVAL + 1)
    with freeze_time(frozen_datetime):
        # Make one server return an error from its list_repositories() call
        mock_method = mock.patch.object(
            initial_reconciled_servers[("dep1", "location2")],
            "create_client",
            return_value=mock.MagicMock(
                list_repositories=lambda: serialize_value(
                    SerializableErrorInfo(
                        message="test error", stack=[], cls_name="TestError", cause=None
                    )
                )
            ),
        )
        mock_method.start()

        user_code_launcher.reconcile()

        # entries are the same because the new code location is redeployed, but the new server is different
        assert user_code_launcher._actual_entries == initial_actual_entries

        new_servers = user_code_launcher.get_grpc_endpoints()
        # locations already in an error unchanged
        assert (
            new_servers[("dep1", "location1")] == initial_reconciled_servers[("dep1", "location1")]
        )
        assert (
            new_servers[("dep1", "location2")] != initial_reconciled_servers[("dep1", "location2")]
        )
        assert (
            new_servers[("dep1", "location3")] == initial_reconciled_servers[("dep1", "location3")]
        )


def test_refresh_actual_entries_multipex(
    user_code_launcher: UserCodeTestLauncher,
):
    """Test that _refresh_actual_entries handles dictionary mutation during iteration."""
    user_code_launcher.start(run_reconcile_thread=False)

    now = time.time()

    # Set up multiple pex locations
    pex_server_one = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now,
    )
    pex_server_two = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="bar.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now,
    )

    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): pex_server_one,
        ("dep1", "location2"): pex_server_two,
    }

    user_code_launcher.update_grpc_metadata(
        metadata_map, control_plane_error_locations=set(), control_plane_outdated_locations=set()
    )
    user_code_launcher.reconcile()

    # Verify both locations are set up with multipex servers
    assert ("dep1", "location1") in user_code_launcher._multipex_servers
    assert ("dep1", "location2") in user_code_launcher._multipex_servers
    assert ("dep1", "location1") in user_code_launcher._actual_entries
    assert ("dep1", "location2") in user_code_launcher._actual_entries

    # Clear pex servers for location1 to simulate them disappearing.
    # This will cause _refresh_actual_entries to call _trigger_recovery_server_restart
    # which removes the entry from _multipex_servers during iteration.
    multipex_server_1 = user_code_launcher._multipex_servers[("dep1", "location1")]
    multipex_server_2 = user_code_launcher._multipex_servers[("dep1", "location2")]
    user_code_launcher._pex_servers[multipex_server_1.server_handle] = []

    # Mock create_multipex_client to return a mock that succeeds on ping,
    # so _refresh_actual_entries proceeds past the health check to the pex server check
    mock_multipex_client = mock.MagicMock()
    with (
        mock.patch.object(
            multipex_server_1.server_endpoint,
            "create_multipex_client",
            return_value=mock_multipex_client,
        ),
        mock.patch.object(
            multipex_server_2.server_endpoint,
            "create_multipex_client",
            return_value=mock_multipex_client,
        ),
    ):
        user_code_launcher._refresh_actual_entries(metadata_map, set(), set(), set())

    # location1 should have been removed from _multipex_servers by _trigger_recovery_server_restart
    assert ("dep1", "location1") not in user_code_launcher._multipex_servers
    # location2 should still be present
    assert ("dep1", "location2") in user_code_launcher._multipex_servers


def test_redeploy_unavailable_server(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start(run_reconcile_thread=False)

    now = get_current_datetime()
    now_timestamp = now.timestamp()

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now_timestamp
    )
    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="bar.py"), now_timestamp
    )

    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep1", "location2"): server_two,
    }

    with freeze_time(now):
        user_code_launcher.update_grpc_metadata(
            metadata_map,
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(),
        )
        user_code_launcher.reconcile()
        user_code_launcher.assert_reconciliation(metadata_map, None, run_reconcile_thread=False)

        reconciled_servers = user_code_launcher.get_grpc_endpoints()

        assert ("dep1", "location1") in reconciled_servers and (
            "dep1",
            "location2",
        ) in reconciled_servers

    # Both servers fail their ping() check (since they are not actually running)
    frozen_datetime = now + datetime.timedelta(seconds=ACTUAL_ENTRIES_REFRESH_INTERVAL + 1)
    with freeze_time(frozen_datetime):
        user_code_launcher.reconcile()

        assert user_code_launcher._first_unavailable_times == {
            ("dep1", "location1"): frozen_datetime.timestamp(),
            ("dep1", "location2"): frozen_datetime.timestamp(),
        }

        first_failure_time = frozen_datetime

        assert reconciled_servers == user_code_launcher.get_grpc_endpoints()

    # Make one server recover on the next check
    frozen_datetime = frozen_datetime + datetime.timedelta(
        seconds=ACTUAL_ENTRIES_REFRESH_INTERVAL + 1
    )
    with freeze_time(frozen_datetime):
        # Make one server recover its ping() check (by returning a Mock that passes ping() without raising an exception)
        mock_method = mock.patch.object(
            reconciled_servers[("dep1", "location1")],
            "create_client",
            return_value=mock.MagicMock(),
        )
        mock_method.start()
        user_code_launcher.reconcile()

        # Other location is still tracking
        assert user_code_launcher._first_unavailable_times == {
            ("dep1", "location2"): first_failure_time.timestamp(),
        }

    frozen_datetime = frozen_datetime + datetime.timedelta(
        user_code_launcher._server_process_startup_timeout + 1
    )
    with freeze_time(frozen_datetime):
        user_code_launcher.reconcile()

        # New server has been created since the server stayed unreachable for long enough
        new_servers = user_code_launcher.get_grpc_endpoints()

        assert new_servers[("dep1", "location1")] == reconciled_servers[("dep1", "location1")]
        assert new_servers[("dep1", "location2")] != reconciled_servers[("dep1", "location2")]


def test_heartbeats(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start(run_reconcile_thread=False)
    assert user_code_launcher.get_grpc_server_heartbeats() == {}

    now = time.time()

    # Add a server
    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )
    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="foo.py"), now
    )

    server_three = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag3", python_file="foo.py"), now + 1
    )

    entry_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep2", "location2"): server_two,
    }

    user_code_launcher.update_grpc_metadata(
        entry_map, control_plane_error_locations=set(), control_plane_outdated_locations=set()
    )

    assert user_code_launcher.get_grpc_server_heartbeats() == {
        "dep1": [
            CloudCodeServerHeartbeat(
                "location1",
                server_status=CloudCodeServerStatus.STARTING,
                error=None,
                metadata={},
            )
        ],
        "dep2": [
            CloudCodeServerHeartbeat(
                "location2",
                server_status=CloudCodeServerStatus.STARTING,
                error=None,
                metadata={},
            )
        ],
    }

    user_code_launcher.reconcile()

    assert user_code_launcher.get_grpc_server_heartbeats() == {
        "dep1": [
            CloudCodeServerHeartbeat(
                "location1",
                server_status=CloudCodeServerStatus.RUNNING,
                error=None,
                metadata={},
            )
        ],
        "dep2": [
            CloudCodeServerHeartbeat(
                "location2",
                server_status=CloudCodeServerStatus.RUNNING,
                error=None,
                metadata={},
            )
        ],
    }
    # Test recovery after adding a server
    user_code_launcher.fail_next_add = True

    entry_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_three,
        ("dep2", "location2"): server_two,
    }

    user_code_launcher.update_grpc_metadata(
        entry_map, control_plane_error_locations=set(), control_plane_outdated_locations=set()
    )
    assert user_code_launcher.get_grpc_server_heartbeats() == {
        "dep1": [
            CloudCodeServerHeartbeat(
                "location1",
                server_status=CloudCodeServerStatus.RUNNING,
                error=None,
                metadata={},
            )
        ],
        "dep2": [
            CloudCodeServerHeartbeat(
                "location2",
                server_status=CloudCodeServerStatus.RUNNING,
                error=None,
                metadata={},
            )
        ],
    }

    user_code_launcher.reconcile()

    heartbeats_with_error = user_code_launcher.get_grpc_server_heartbeats()

    assert len(heartbeats_with_error) == 2
    assert len(heartbeats_with_error["dep1"]) == 1
    assert heartbeats_with_error["dep1"][0].location_name == "location1"
    assert heartbeats_with_error["dep1"][0].server_status == CloudCodeServerStatus.FAILED
    assert "Server add failed" in str(heartbeats_with_error["dep1"][0].error)

    assert heartbeats_with_error["dep2"] == [
        CloudCodeServerHeartbeat(
            "location2",
            server_status=CloudCodeServerStatus.RUNNING,
            error=None,
            metadata={},
        )
    ]

    # Test with truncation
    with environ({"DAGSTER_CLOUD_CODE_SERVER_HEARTBEAT_ERROR_SIZE_LIMIT": "15"}):
        heartbeats_with_error = user_code_launcher.get_grpc_server_heartbeats()
        assert len(heartbeats_with_error) == 2
        assert len(heartbeats_with_error["dep1"]) == 1
        assert heartbeats_with_error["dep1"][0].location_name == "location1"
        assert heartbeats_with_error["dep1"][0].server_status == CloudCodeServerStatus.FAILED
        assert "Exception: Serv (TRUNCATED)" in str(heartbeats_with_error["dep1"][0].error)


def test_updating_metadata_without_timestamp_does_not_update_code_server(
    user_code_launcher: UserCodeTestLauncher,
):
    user_code_launcher.start()

    now = time.time()

    assert user_code_launcher.get_active_grpc_server_handles() == []

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )
    _check_update(user_code_launcher, {("dep1", "location1"): server_one})

    assert len(user_code_launcher.get_active_grpc_server_handles()) == 1

    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1", python_file="foo.py", cloud_context_env={"FOO": "BAR"}
        ),
        now,
    )

    # since only cloud context env changed, nothing updates
    _check_update(
        user_code_launcher,
        {("dep1", "location1"): server_two},
        expected_entry_map={("dep1", "location1"): server_one},
    )


def test_reconciliation(user_code_launcher: UserCodeTestLauncher, caplog: pytest.LogCaptureFixture):
    user_code_launcher.start()

    now = time.time()

    caplog.clear()

    assert user_code_launcher.get_active_grpc_server_handles() == []

    # Add a server
    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )
    _check_update(user_code_launcher, {("dep1", "location1"): server_one})

    assert (
        caplog.text.count(
            f"Reconciling to reach {{(dep1, location1, {now})}}. To add: {{(dep1, location1,"
            f" {now})}}. To update: {{}}. To remove: {{}}. To upload: {{}}."
        )
        == 1
    )

    assert len(user_code_launcher.get_active_grpc_server_handles()) == 1

    caplog.clear()

    # Update a server to a new image
    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="foo.py"), now + 1
    )
    _check_update(user_code_launcher, {("dep1", "location1"): server_two})

    assert (
        caplog.text.count(
            f"Reconciling to reach {{(dep1, location1, {server_two.update_timestamp})}}. To add: {{}}. To update: {{(dep1,"
            f" location1, {server_two.update_timestamp})}}. To remove: {{}}. To upload: {{}}."
        )
        == 1
    )

    assert len(user_code_launcher.get_active_grpc_server_handles()) == 1

    caplog.clear()

    # Add a second server
    server_three = UserCodeLauncherEntry(
        CodeLocationDeployData("test_another_image:tag3", python_file="bar.py"), now + 2
    )
    _check_update(
        user_code_launcher,
        {
            ("dep1", "location1"): server_two,
            ("dep1", "location2"): server_three,
        },
    )

    assert (
        caplog.text.count(
            f"Reconciling to reach {{(dep1, location1, {server_two.update_timestamp}), (dep1, location2, {server_three.update_timestamp})}}. To add:"
            f" {{(dep1, location2, {server_three.update_timestamp})}}. To update: {{}}. To remove: {{}}. To upload: {{}}."
        )
        == 1
    )

    assert len(user_code_launcher.get_active_grpc_server_handles()) == 2

    caplog.clear()

    # Remove a server
    _check_update(user_code_launcher, {("dep1", "location2"): server_three})

    assert (
        caplog.text.count(
            f"Reconciling to reach {{(dep1, location2, {server_three.update_timestamp})}}. To add: {{}}. To update: {{}}. To"
            f" remove: {{(dep1, location1, {server_two.update_timestamp})}}. To upload: {{}}."
        )
        == 1
    )

    assert len(user_code_launcher.get_active_grpc_server_handles()) == 1

    # Since we didn't specify any locations should be uploaded, none were
    assert user_code_launcher.uploaded_locations == []


def test_new_timestamp_refreshes_server(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start()

    now = time.time()

    metadata = CodeLocationDeployData("test_image:tag1", python_file="foo.py")

    server_one = UserCodeLauncherEntry(metadata, now)
    _check_update(user_code_launcher, {("dep1", "location1"): server_one})

    current_endpoint = user_code_launcher.get_grpc_endpoint("dep1", "location1")
    _check_update(user_code_launcher, {("dep1", "location1"): server_one})
    assert user_code_launcher.get_grpc_endpoint("dep1", "location1").port == current_endpoint.port

    # Increasing timestamp causes the server to be reloaded
    _check_update(
        user_code_launcher,
        {("dep1", "location1"): UserCodeLauncherEntry(metadata, now + 1)},
    )
    assert (
        user_code_launcher.get_grpc_endpoint(
            "dep1",
            "location1",
        ).port
        != current_endpoint.port
    )

    assert user_code_launcher.uploaded_locations == []


def test_graphql_write_failure(
    caplog: pytest.LogCaptureFixture, user_code_launcher: UserCodeTestLauncher
):
    user_code_launcher.fail_graphql_writes = True

    user_code_launcher.start()

    now = time.time()

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )
    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="bar.py"), now
    )

    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep1", "location2"): server_two,
    }

    user_code_launcher.add_upload_metadata_for_deployment(
        "dep1",
        upload_metadata=metadata_map,
        control_plane_error_locations=set(),
        control_plane_outdated_locations=set(metadata_map.keys()),
    )
    user_code_launcher.wait_for_reconcile()

    # graphql fails, but the metadata updates
    user_code_launcher.assert_reconciliation(metadata_map)

    assert caplog.text.count("Fetching metadata for ") == 2
    assert caplog.text.count("Error while writing location data") == 2

    caplog.clear()

    user_code_launcher.wait_for_reconcile()
    assert caplog.text.count("Error while writing location data") == 0

    assert user_code_launcher.uploaded_locations == []


def test_add_upload_metadata_retains_other_deployments(
    user_code_launcher: UserCodeTestLauncher,
):
    """Test that add_upload_metadata_for_deployment only replaces error/outdated
    state for the given deployment, preserving state for other deployments.
    """
    user_code_launcher.start(run_reconcile_thread=False)

    now = time.time()
    dep1_loc = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )
    dep2_loc = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="bar.py"), now
    )

    # Set up initial state with two deployments via update_grpc_metadata
    # (which replaces all state)
    user_code_launcher.update_grpc_metadata(
        {("dep1", "location1"): dep1_loc, ("dep2", "location1"): dep2_loc},
        control_plane_error_locations={("dep2", "location1")},
        control_plane_outdated_locations={("dep1", "location1")},
    )

    assert user_code_launcher._control_plane_error_locations == {("dep2", "location1")}
    assert user_code_launcher._control_plane_outdated_locations == {("dep1", "location1")}

    # Now add upload metadata for dep1 only — dep2's error/outdated state must be retained
    dep1_loc_updated = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1_v2", python_file="foo.py"), now + 1
    )
    user_code_launcher.add_upload_metadata_for_deployment(
        "dep1",
        upload_metadata={("dep1", "location1"): dep1_loc_updated},
        control_plane_error_locations={("dep1", "location1")},
        control_plane_outdated_locations=set(),
    )

    # dep1's error/outdated state was replaced: dep1 location1 now has error, no outdated
    # dep2's state was preserved: dep2 location1 still has error from before
    assert user_code_launcher._control_plane_error_locations == {
        ("dep1", "location1"),
        ("dep2", "location1"),
    }
    # dep1's outdated was cleared (we passed empty set for dep1), dep2 had no outdated
    assert user_code_launcher._control_plane_outdated_locations == set()

    # Now add upload metadata for dep2 — dep1's state must be retained
    user_code_launcher.add_upload_metadata_for_deployment(
        "dep2",
        upload_metadata={("dep2", "location1"): dep2_loc},
        control_plane_error_locations=set(),
        control_plane_outdated_locations={("dep2", "location1")},
    )

    # dep1's error state preserved, dep2's error cleared
    assert user_code_launcher._control_plane_error_locations == {("dep1", "location1")}
    # dep2's outdated set, dep1 had no outdated
    assert user_code_launcher._control_plane_outdated_locations == {("dep2", "location1")}


def test_graphql_uploads(
    caplog: pytest.LogCaptureFixture, user_code_launcher: UserCodeTestLauncher
):
    user_code_launcher.start()

    now = time.time()

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )

    metadata_two = CodeLocationDeployData("test_image:tag2", python_file="foo.py")

    server_two = UserCodeLauncherEntry(metadata_two, now)

    _check_update(
        user_code_launcher, {("dep1", "location1"): server_one, ("dep1", "location2"): server_two}
    )

    server_two_new_timestamp = UserCodeLauncherEntry(metadata_two, now + 1)

    server_three = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag3", python_file="foo.py"), now
    )

    # Tell the launcher to upload location1 (no changes), location2 (same metadata, new timestamp),
    # and location3 (brand new location). All three should be uploaded as part of the
    # reconciliation

    caplog.clear()

    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep1", "location2"): server_two_new_timestamp,
        ("dep1", "location3"): server_three,
    }
    user_code_launcher.add_upload_metadata_for_deployment(
        "dep1",
        metadata_map,
        control_plane_error_locations=set(),
        control_plane_outdated_locations=set(metadata_map.keys()),
    )

    user_code_launcher.wait_for_reconcile()

    user_code_launcher.assert_reconciliation(metadata_map)

    assert sorted(user_code_launcher.uploaded_locations) == sorted(
        ["location1", "location2", "location3"]
    )

    assert (
        caplog.text.count(
            f"Reconciling to reach {{(dep1, location1, {now}), (dep1, location2, {now + 1}), (dep1,"
            f" location3, {now})}}. To add: {{(dep1, location3, {now})}}. To update: {{(dep1,"
            f" location2, {now + 1})}}. To remove: {{}}. To upload: {{(dep1, location1, {now}),"
            f" (dep1, location2, {now + 1}), (dep1, location3, {now})}}."
        )
        == 1
    )

    for location in ["location1", "location2", "location3"]:
        assert caplog.text.count(f"Fetching metadata for dep1:{location}") == 1

    # only uploads once

    caplog.clear()
    user_code_launcher.wait_for_reconcile()
    assert caplog.text.count("Fetching metadata for") == 0

    assert sorted(user_code_launcher.uploaded_locations) == sorted(
        ["location1", "location2", "location3"]
    )


def test_launcher_invalid_images(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start()

    now = time.time()

    server_with_invalid_image = UserCodeLauncherEntry(
        CodeLocationDeployData(python_file="foo.py", image="trailing_whitespace "),
        now,
    )
    expected_errors = {("dep1", "location1"): "Images must not have leading or trailing whitespace"}

    _check_update(
        user_code_launcher,
        {("dep1", "location1"): server_with_invalid_image},
        expected_entry_map={},
        agent_error_map=expected_errors,
    )

    server_with_invalid_image = UserCodeLauncherEntry(
        CodeLocationDeployData(python_file="foo.py", image="  leading_whitespace"),
        now,
    )

    _check_update(
        user_code_launcher,
        {("dep1", "location1"): server_with_invalid_image},
        expected_entry_map={},
        agent_error_map=expected_errors,
    )


def test_launcher_requires_images(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start()
    assert user_code_launcher.requires_images

    now = time.time()

    server_without_image = UserCodeLauncherEntry(CodeLocationDeployData(python_file="foo.py"), now)
    expected_errors = {
        ("dep1", "location1"): "Your agent's configuration requires you to specify an image."
    }

    _check_update(
        user_code_launcher,
        {("dep1", "location1"): server_without_image},
        expected_entry_map={},
        agent_error_map=expected_errors,
    )

    # updating to a server with image works though
    server_with_image = UserCodeLauncherEntry(
        CodeLocationDeployData(python_file="foo.py", image="now_with_image"), now + 1
    )
    _check_update(user_code_launcher, {("dep1", "location1"): server_with_image})

    # updating back from image to no image fails
    _check_update(
        user_code_launcher,
        {("dep1", "location1"): server_without_image._replace(update_timestamp=now + 2)},
        expected_entry_map={},
        agent_error_map=expected_errors,
    )


def test_launcher_without_images(user_code_launcher_no_images):
    user_code_launcher_no_images.start()
    assert not user_code_launcher_no_images.requires_images

    now = time.time()

    server_without_image = UserCodeLauncherEntry(CodeLocationDeployData(python_file="foo.py"), now)
    _check_update(user_code_launcher_no_images, {("dep1", "location1"): server_without_image})

    updated_server_without_image = UserCodeLauncherEntry(
        CodeLocationDeployData(python_file="bar.py"), now + 1
    )
    _check_update(
        user_code_launcher_no_images, {("dep1", "location1"): updated_server_without_image}
    )

    server_with_image = UserCodeLauncherEntry(
        CodeLocationDeployData(python_file="foo.py", image="now_with_image"), now + 2
    )
    # updating to a server with an image fails

    error_message = "Your agent's configuration cannot load locations that specify a Docker image."

    _check_update(
        user_code_launcher_no_images,
        {("dep1", "location1"): server_with_image},
        expected_entry_map={},
        agent_error_map={("dep1", "location1"): error_message},
    )

    updated_server_without_image = updated_server_without_image._replace(update_timestamp=now + 3)

    # updating back to a server without an image works
    _check_update(
        user_code_launcher_no_images, {("dep1", "location1"): updated_server_without_image}
    )

    server_with_image = server_with_image._replace(update_timestamp=now + 4)

    # can't add a server with an image
    _check_update(
        user_code_launcher_no_images,
        {
            ("dep1", "location1"): updated_server_without_image,
            ("dep1", "location2"): server_with_image,
        },
        expected_entry_map={("dep1", "location1"): updated_server_without_image},
        agent_error_map={("dep1", "location2"): error_message},
    )


def test_cleanup_after_add_failure(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start()

    now = time.time()

    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )

    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="foo.py"), now + 1
    )

    _check_update(user_code_launcher, {("dep1", "location1"): server_one})

    assert len(user_code_launcher.servers[("dep1", "location1")]) == 1

    user_code_launcher.fail_next_add_after_server_added = {"location1"}

    _check_update(
        user_code_launcher,
        {("dep1", "location1"): server_two},
        expected_entry_map={},
        agent_error_map={("dep1", "location1"): "Server add failed after creating the server"},
    )

    # Old server is cleaned up after the failure, new server stays in an error state
    assert len(user_code_launcher.servers[("dep1", "location1")]) == 1


def test_truncate_uploaded_entries(user_code_launcher: UserCodeTestLauncher):
    # Verify that the error is truncated
    user_code_launcher.start()

    now = time.time()
    server = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="foo.py"), now
    )
    with environ({"DAGSTER_CLOUD_CODE_LOCATION_UPLOAD_ERROR_SIZE_LIMIT": "25"}):
        metadata_map = {("dep1", "location1"): server}
        user_code_launcher.add_upload_metadata_for_deployment(
            "dep1",
            upload_metadata=metadata_map,
            control_plane_error_locations=set(),
            control_plane_outdated_locations=set(metadata_map.keys()),
        )

        user_code_launcher.fail_next_add_after_server_added = {"location1"}

        _check_update(
            user_code_launcher,
            metadata_map,
            expected_entry_map={},
            agent_error_map={("dep1", "location1"): "Server add failed after creating the server"},
        )

        assert len(user_code_launcher.uploaded_entries) == 1
        assert user_code_launcher.uploaded_entries[0].serialized_error_info

        assert (
            "Exception: Server add fai (TRUNCATED)"
            in user_code_launcher.uploaded_entries[0].serialized_error_info.message
        )


def test_failure_recovery(
    caplog: pytest.LogCaptureFixture, user_code_launcher: UserCodeTestLauncher
):
    user_code_launcher.start()

    now = time.time()

    # Add a server
    server_one = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag1", python_file="foo.py"), now
    )
    _check_update(user_code_launcher, {("dep1", "location1"): server_one})

    server_two = UserCodeLauncherEntry(
        CodeLocationDeployData("test_image:tag2", python_file="bar.py"), now
    )

    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep1", "location2"): server_two,
    }

    # Test recovery after adding a server
    user_code_launcher.fail_next_add = True

    # location2 is new — server doesn't have data for it yet
    user_code_launcher.update_grpc_metadata(
        metadata_map,
        control_plane_error_locations=set(),
        control_plane_outdated_locations={("dep1", "location2")},
    )
    user_code_launcher.wait_for_reconcile()

    # Immediately update control_plane_error_locations to reflect that the server now knows
    # about location2's error (agent uploaded it). This prevents the recovery mechanism
    # from retrying on the next reconcile cycle.
    location2_error = {("dep1", "location2")}
    user_code_launcher.update_grpc_metadata(
        metadata_map,
        control_plane_error_locations=location2_error,
        control_plane_outdated_locations=set(),
    )

    assert caplog.text.count("Error while updating server for dep1:location2") == 1

    expected_metadata_map: UserCodeLauncherEntryMap = {("dep1", "location1"): server_one}
    expected_errors = {("dep1", "location2"): "Server add failed"}

    # Don't wait for another reconcile - just check current state
    user_code_launcher.assert_reconciliation(
        expected_metadata_map, expected_errors, run_reconcile_thread=False
    )

    # Retry keeps in the same state since metadata did not change.
    _check_update(
        user_code_launcher,
        metadata_map,
        expected_metadata_map,
        expected_errors,
        control_plane_error_locations=location2_error,
    )

    # But changing the metadata causes the location to reload again
    server_three = UserCodeLauncherEntry(
        CodeLocationDeployData("test_another_image:tag3", python_file="bar.py"), now + 1
    )

    metadata_map: UserCodeLauncherEntryMap = {
        ("dep1", "location1"): server_one,
        ("dep1", "location2"): server_three,
    }
    _check_update(user_code_launcher, metadata_map, control_plane_error_locations=location2_error)

    # Test recovery after updating server metadata if add fails
    server_four = UserCodeLauncherEntry(
        CodeLocationDeployData("test_another_image:tag3", python_file="bar.py"), now + 2
    )
    metadata_map = {("dep1", "location1"): server_four, ("dep1", "location2"): server_three}

    user_code_launcher.fail_next_add = True
    # location1 has new timestamp — server data is stale
    user_code_launcher.update_grpc_metadata(
        metadata_map,
        control_plane_error_locations=set(),
        control_plane_outdated_locations={("dep1", "location1")},
    )
    user_code_launcher.wait_for_reconcile()

    # Immediately update control_plane_error_locations to reflect that the server now knows
    # about location1's error (agent uploaded it).
    location1_error = {("dep1", "location1")}
    user_code_launcher.update_grpc_metadata(
        metadata_map,
        control_plane_error_locations=location1_error,
        control_plane_outdated_locations=set(),
    )

    expected_metadata_map = {("dep1", "location2"): server_three}
    expected_errors = {("dep1", "location1"): "Server add failed"}

    # Don't wait for another reconcile - just check current state
    user_code_launcher.assert_reconciliation(
        expected_metadata_map, expected_errors, run_reconcile_thread=False
    )

    # Retry keeps in the same state since timestamp did not change.
    _check_update(
        user_code_launcher,
        metadata_map,
        expected_metadata_map,
        expected_errors,
        control_plane_error_locations=location1_error,
    )

    # But changing the timestamp causes the location to reload again
    server_five = UserCodeLauncherEntry(
        CodeLocationDeployData("test_another_image:tag3", python_file="bar.py"), now + 3
    )
    metadata_map = {("dep1", "location1"): server_five, ("dep1", "location2"): server_three}

    _check_update(user_code_launcher, metadata_map, control_plane_error_locations=location1_error)

    caplog.clear()

    # Test recovery after updating server metadata if remove fails
    metadata_map = {("dep1", "location1"): server_five, ("dep1", "location2"): server_two}
    user_code_launcher.fail_next_remove = True

    # Despite the error, metadata map is unchanged (but there is an error logged)
    _check_update(user_code_launcher, metadata_map)

    assert (
        caplog.text.count("Error while cleaning up after updating server for dep1:location2") == 1
    )

    caplog.clear()

    # Retry keeps in the same state since metadata did not change
    _check_update(user_code_launcher, metadata_map)

    assert (
        caplog.text.count("Error while cleaning up after updating server for dep1:location2") == 0
    )

    # But changing the timestamp causes the location to reload again
    metadata_map = {("dep1", "location1"): server_five, ("dep1", "location2"): server_three}
    _check_update(user_code_launcher, metadata_map)

    # Test recovery after deleting server metadata
    metadata_map = {("dep1", "location2"): server_three}
    user_code_launcher.fail_next_remove = True

    caplog.clear()

    user_code_launcher.update_grpc_metadata(
        metadata_map, control_plane_error_locations=set(), control_plane_outdated_locations=set()
    )
    user_code_launcher.wait_for_reconcile()

    # Despite the error, metadata map is unchanged (but an error is logged)
    user_code_launcher.assert_reconciliation(metadata_map)

    assert caplog.text.count("Error while removing server for dep1:location1") == 1

    # Retry updates to expected state
    _check_update(user_code_launcher, metadata_map)


def test_can_register_instance(user_code_launcher: UserCodeTestLauncher):
    assert isinstance(
        # We are accessing a private property in this test, but
        # in practice this property is always accessed from within
        # the class itself.
        user_code_launcher._instance,
        DagsterInstance,
    )


def test_dont_upload_on_start(user_code_launcher, monkeypatch):
    mock_gql_response = {
        "data": {
            "workspace": {
                "workspaceEntries": [
                    {"locationName": "test-location"},
                ],
            },
        },
    }
    monkeypatch.setattr(
        "dagster_cloud_cli.core.graphql_client.DagsterCloudGraphQLClient.execute",
        lambda *args, **kwargs: mock_gql_response,
    )

    # Typically, we don't upload on start
    user_code_launcher.start()
    assert not user_code_launcher._upload_locations


def test_pex_metadata(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start()

    now = time.time()

    # Add a pex location (which should create a multipex server and a grpc server subprocess on it)
    pex_server_one = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_one})
    assert len(user_code_launcher.multipex_server_handles) == 1

    multipex_server = user_code_launcher.multipex_server_handles[("dep1", "location1")]

    pex_servers = user_code_launcher._get_existing_pex_servers("dep1", "location1").copy()
    assert len(pex_servers) == 1

    # operation is idempotent
    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_one})
    assert len(user_code_launcher.multipex_server_handles) == 1
    assert user_code_launcher._get_existing_pex_servers("dep1", "location1") == pex_servers

    assert user_code_launcher.multipex_server_handles[("dep1", "location1")] == multipex_server

    new_now = now + 10.5

    # update to a new location with the same base image (same multipex server, new grpc server)
    pex_server_two = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        new_now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_two})

    # Multipex server unchanged
    assert user_code_launcher.multipex_server_handles[("dep1", "location1")] == multipex_server

    # Pex server changed
    new_pex_servers = user_code_launcher._get_existing_pex_servers("dep1", "location1")
    assert len(new_pex_servers) == 1
    assert new_pex_servers != pex_servers

    new_now = now + 20.5

    # Changing the base image, though, does swap out the multipex server
    pex_server_three = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag2",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        new_now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_three})
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 1
    assert user_code_launcher.multipex_server_handles[("dep1", "location1")] != multipex_server

    assert user_code_launcher._get_existing_pex_servers("dep1", "location1")

    # Using a python version instead of an image tag changes out the multipex server
    multipex_server = user_code_launcher.multipex_server_handles[("dep1", "location1")]
    new_now = new_now + 1

    pex_server_four = UserCodeLauncherEntry(
        CodeLocationDeployData(
            None,
            python_file="foo.py",
            pex_metadata=PexMetadata(
                pex_tag="files=deps-hash.pex:source-hash.pex", python_version="3.9"
            ),
        ),
        new_now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_four})
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 1
    assert user_code_launcher.multipex_server_handles[("dep1", "location1")] != multipex_server

    assert user_code_launcher._get_existing_pex_servers("dep1", "location1")

    # Same pex tag with new python version changes the multipex server
    multipex_server = user_code_launcher.multipex_server_handles[("dep1", "location1")]
    new_now = new_now + 1

    pex_server_five = UserCodeLauncherEntry(
        CodeLocationDeployData(
            None,
            python_file="foo.py",
            pex_metadata=PexMetadata(
                pex_tag="files=deps-hash.pex:source-hash.pex", python_version="3.12"
            ),
        ),
        new_now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_five})
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 1
    assert user_code_launcher.multipex_server_handles[("dep1", "location1")] != multipex_server
    assert user_code_launcher._get_existing_pex_servers("dep1", "location1")

    # Same python version with a new pex tag reuses the multipex server
    multipex_server = user_code_launcher.multipex_server_handles[("dep1", "location1")]
    new_now = new_now + 40

    pex_server_six = UserCodeLauncherEntry(
        CodeLocationDeployData(
            None,
            python_file="foo.py",
            pex_metadata=PexMetadata(
                pex_tag="files=deps-hash2.pex:source-hash.pex", python_version="3.12"
            ),
        ),
        new_now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_six})
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 1
    assert user_code_launcher.multipex_server_handles[("dep1", "location1")] == multipex_server
    assert user_code_launcher._get_existing_pex_servers("dep1", "location1")

    new_now = new_now + 20.5

    # Add a second location

    _check_update(
        user_code_launcher,
        {("dep1", "location1"): pex_server_three, ("dep1", "location2"): pex_server_two},
    )

    assert len(user_code_launcher.multipex_server_handles) == 2

    # Remove a server

    assert ("dep1", "location1") in user_code_launcher._multipex_servers
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location2")]) == 1
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 1

    _check_update(user_code_launcher, {("dep1", "location2"): pex_server_two})
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location2")]) == 1
    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 0

    assert ("dep1", "location1") not in user_code_launcher._multipex_servers

    # Simulate the case where the loop decides that the pex server has become unavailable adn
    # redeploys it

    old_multipex_handles = user_code_launcher.multipex_server_handles[("dep1", "location2")]

    del user_code_launcher._actual_entries[("dep1", "location2")]
    del user_code_launcher._multipex_servers[("dep1", "location2")]

    _check_update(user_code_launcher, {("dep1", "location2"): pex_server_two})

    # new multipex server spins up

    assert len(user_code_launcher.multipex_server_handles[("dep1", "location2")]) == 1
    assert user_code_launcher.multipex_server_handles[("dep1", "location2")] != old_multipex_handles


def test_pex_failure_recovery_on_add(
    caplog: pytest.LogCaptureFixture, user_code_launcher: UserCodeTestLauncher
):
    # Issue spinning up a multipex server recovers, returns a clear error

    user_code_launcher.start()

    now = time.time()

    pex_server_one = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now,
    )

    user_code_launcher.fail_next_add = True

    metadata_map = {("dep1", "location1"): pex_server_one}
    # location1 is new — server doesn't have data for it yet
    user_code_launcher.update_grpc_metadata(
        metadata_map,
        control_plane_error_locations=set(),
        control_plane_outdated_locations={("dep1", "location1")},
    )
    user_code_launcher.wait_for_reconcile()

    # Immediately update control_plane_error_locations to prevent recovery on the next cycle.
    location1_error = {("dep1", "location1")}
    user_code_launcher.update_grpc_metadata(
        metadata_map,
        control_plane_error_locations=location1_error,
        control_plane_outdated_locations=set(),
    )

    assert caplog.text.count("Error while setting up multipex server for") == 1

    expected_errors = {("dep1", "location1"): "Server add failed"}

    user_code_launcher.assert_reconciliation({}, expected_errors, run_reconcile_thread=False)

    # Recovers when you redeploy (by increasing tiemstamp)
    pex_server_two = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now + 10,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_two})

    multipex_server = user_code_launcher._multipex_servers[("dep1", "location1")]

    # Server becomes unavailable - new multipex server should spin up

    user_code_launcher.fail_next_multipex_health_check = True

    pex_server_three = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now + 20,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_three})

    assert (
        caplog.text.count(
            "Spinning up a new multipex server for dep1:location1 since the existing one failed"
        )
        == 1
    )

    # New server does in fact exist and is different than the old one
    new_multipex_server = user_code_launcher._multipex_servers[("dep1", "location1")]
    assert new_multipex_server != multipex_server

    # idempotent afterwards

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_three})
    assert user_code_launcher._multipex_servers[("dep1", "location1")] == new_multipex_server


def test_pex_failure_waiting_for_new_server(
    caplog: pytest.LogCaptureFixture, user_code_launcher: UserCodeTestLauncher
):
    user_code_launcher.start()

    now = time.time()

    pex_server_one = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now,
    )

    user_code_launcher.fail_next_add_after_server_added = {"location1"}

    _check_update(
        user_code_launcher,
        {("dep1", "location1"): pex_server_one},
        expected_entry_map={},
        agent_error_map={("dep1", "location1"): "Server add failed after creating the server"},
    )

    assert caplog.text.count("Error while waiting for multipex server for dep1:location1") == 1

    # Recovers when you redeploy (by increasing tiemstamp)
    pex_server_two = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now + 10,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_two})


def test_change_from_multipex_to_pex(user_code_launcher: UserCodeTestLauncher):
    user_code_launcher.start()

    now = time.time()

    pex_server_one = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
            pex_metadata=PexMetadata(pex_tag="files=deps-hash.pex:source-hash.pex"),
        ),
        now,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): pex_server_one})

    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 1

    non_pex_server = UserCodeLauncherEntry(
        CodeLocationDeployData(
            "test_image:tag1",
            python_file="foo.py",
        ),
        now + 10,
    )

    _check_update(user_code_launcher, {("dep1", "location1"): non_pex_server})

    assert len(user_code_launcher.multipex_server_handles[("dep1", "location1")]) == 0

    assert not user_code_launcher._multipex_servers.get(("dep1", "location1"))
