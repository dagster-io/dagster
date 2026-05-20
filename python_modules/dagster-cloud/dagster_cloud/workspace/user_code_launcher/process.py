import logging
import os
import subprocess
import sys
import threading
from collections import defaultdict
from collections.abc import Collection, Mapping
from typing import Any, NamedTuple

from dagster import (
    BoolSource,
    Field,
    IntSource,
    _check as check,
)
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._grpc.client import DagsterGrpcClient, client_heartbeat_thread
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import find_free_port, safe_tempfile_path_unmanaged
from dagster._utils.merger import merge_dicts
from dagster_shared import seven
from dagster_shared.ipc import open_ipc_subprocess
from typing_extensions import Self

from dagster_cloud.api.dagster_cloud_api import UserCodeDeploymentType
from dagster_cloud.execution.cloud_run_launcher.process import CloudProcessRunLauncher
from dagster_cloud.execution.monitoring import CloudContainerResourceLimits
from dagster_cloud.pex.grpc import MultiPexGrpcClient
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
    DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
    SHARED_USER_CODE_LAUNCHER_CONFIG,
    DagsterCloudGrpcServer,
    DagsterCloudUserCodeLauncher,
    ServerEndpoint,
    UserCodeLauncherEntry,
)
from dagster_cloud.workspace.user_code_launcher.utils import get_grpc_server_env

CLEANUP_ZOMBIE_PROCESSES_INTERVAL = 5


class ProcessUserCodeEntry(
    NamedTuple(
        "_ProcessUserCodeEntry",
        [
            ("grpc_server_process", subprocess.Popen),
            ("grpc_client", DagsterGrpcClient),
            ("heartbeat_shutdown_event", threading.Event),
            ("heartbeat_thread", threading.Thread),
        ],
    )
):
    def __new__(
        cls,
        grpc_server_process: subprocess.Popen,
        grpc_client: DagsterGrpcClient,
        heartbeat_shutdown_event: threading.Event,
        heartbeat_thread: threading.Thread,
    ):
        return super().__new__(
            cls,
            check.inst_param(grpc_server_process, "grpc_server_process", subprocess.Popen),
            check.inst_param(grpc_client, "grpc_client", DagsterGrpcClient),
            check.inst_param(heartbeat_shutdown_event, "heartbeat_shutdown_event", threading.Event),
            check.inst_param(heartbeat_thread, "heartbeat_thread", threading.Thread),
        )


class MultipexUserCodeEntry(
    NamedTuple(
        "_MultipexUserCodeEntry",
        [
            ("grpc_server_process", subprocess.Popen),
            ("grpc_client", MultiPexGrpcClient),
        ],
    )
):
    def __new__(
        cls,
        grpc_server_process: subprocess.Popen,
        grpc_client: MultiPexGrpcClient,
    ):
        return super().__new__(
            cls,
            check.inst_param(grpc_server_process, "grpc_server_process", subprocess.Popen),
            check.inst_param(grpc_client, "grpc_client", MultiPexGrpcClient),
        )


class ProcessUserCodeLauncher(DagsterCloudUserCodeLauncher, ConfigurableClass):
    def __init__(
        self,
        inst_data: ConfigurableClassData | None = None,
        wait_for_processes: bool = False,
        **kwargs,
    ):
        self._inst_data = inst_data
        self._logger = logging.getLogger("ProcessUserCodeLauncher")

        # map from pid to server being spun up
        # (including old servers in the process of being shut down)
        self._process_entries: dict[int, ProcessUserCodeEntry | MultipexUserCodeEntry] = {}

        # map from locationname to the pid(s) for that location-metadata combination.
        # Generally there should be only one pid per location unless an exception was raised partway
        # through an update
        self._active_pids: dict[tuple[str, str], set[int]] = defaultdict(set)

        self._active_multipex_pids: dict[tuple[str, str], set[int]] = defaultdict(set)

        self._heartbeat_ttl = 60
        self._wait_for_processes = wait_for_processes

        self._cleanup_zombies_shutdown_event = threading.Event()
        self._cleanup_zombies_thread = None

        self._run_launcher: CloudProcessRunLauncher | None = None

        super().__init__(**kwargs)

    @property
    def requires_images(self) -> bool:
        return False

    def get_code_server_resource_limits(
        self, deployment_name: str, location_name: str
    ) -> CloudContainerResourceLimits:
        import psutil

        return {
            "process": {
                "cpu_limit": str(os.cpu_count()),
                "memory_limit": str(psutil.virtual_memory().total),
            },
        }

    def start(self, run_reconcile_thread=True, run_metrics_thread=True):
        super().start(
            run_reconcile_thread=run_reconcile_thread, run_metrics_thread=run_metrics_thread
        )
        # TODO Identify if zombie processes are an issue on Windows and what
        # the proper way to clean them up is
        if sys.platform != "win32":
            self._cleanup_zombies_thread = threading.Thread(
                target=self._cleanup_zombie_processes,
                args=(self._cleanup_zombies_shutdown_event,),
                name="cleanup-zombie-processes",
                daemon=True,
            )
            self._cleanup_zombies_thread.start()

    def _cleanup_zombie_processes(self, shutdown_event):
        while True:
            shutdown_event.wait(CLEANUP_ZOMBIE_PROCESSES_INTERVAL)
            if shutdown_event.is_set():
                break

            # Clean up any child processes that have finished since last check
            while True:
                # This may need to be different on Windows because process groups are
                # handled differently.
                try:
                    # https://docs.python.org/3/library/os.html#os.waitpid
                    # If pid is -1, the request pertains to any child of the current process.
                    pid, _exit_code = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    # Raised when there are no child processes
                    break

                if pid == 0:
                    break

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls) -> dict:
        return merge_dicts(
            {
                "server_process_startup_timeout": Field(
                    IntSource,
                    is_required=False,
                    default_value=DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
                    description=(
                        "Timeout when waiting for a code server to be ready after it is created"
                    ),
                ),
                "wait_for_processes": Field(
                    BoolSource,
                    is_required=False,
                    default_value=False,
                    description=(
                        "When cleaning up the agent, wait for any subprocesses to "
                        "finish before shutting down. Generally only needed in tests/automation."
                    ),
                ),
                "code_server_metrics": Field(
                    {"enabled": Field(bool, is_required=False, default_value=False)},
                    is_required=False,
                ),
                "agent_metrics": Field(
                    {"enabled": Field(bool, is_required=False, default_value=False)},
                    is_required=False,
                ),
            },
            SHARED_USER_CODE_LAUNCHER_CONFIG,
        )

    @property
    def user_code_deployment_type(self) -> UserCodeDeploymentType:
        return UserCodeDeploymentType.PROCESS

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    def _start_new_server_spinup(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
    ) -> DagsterCloudGrpcServer:
        metadata = desired_entry.code_location_deploy_data

        key = (deployment_name, location_name)

        client: MultiPexGrpcClient | DagsterGrpcClient

        port: int | None = None
        socket: str | None = None

        if seven.IS_WINDOWS:
            port = find_free_port()
            socket = None
        else:
            port = None
            socket = safe_tempfile_path_unmanaged()

        if metadata.pex_metadata:
            multipex_process = open_ipc_subprocess(
                metadata.get_multipex_server_command(
                    port,
                    socket,
                    metrics_enabled=self._instance.user_code_launcher.code_server_metrics_enabled,
                )
            )

            pid = multipex_process.pid

            client = MultiPexGrpcClient(port=port, socket=socket)

            self._process_entries[pid] = MultipexUserCodeEntry(
                multipex_process,
                client,
            )

            self._active_multipex_pids[key].add(pid)
        else:
            subprocess_args = metadata.get_grpc_server_command(
                metrics_enabled=self._instance.user_code_launcher.code_server_metrics_enabled
            ) + [
                "--heartbeat",
                "--heartbeat-timeout",
                str(self._heartbeat_ttl),
            ]

            additional_env = get_grpc_server_env(
                metadata,
                port=port,
                location_name=location_name,
                instance_ref=self._instance.ref_for_deployment(deployment_name),
                socket=socket,
            )

            server_process = open_ipc_subprocess(
                subprocess_args,
                env={
                    **os.environ,
                    **{key: str(value) for key, value in metadata.cloud_context_env.items()},
                    **additional_env,
                },
            )
            client = DagsterGrpcClient(
                port=port,
                socket=socket,
                host="localhost",
                use_ssl=False,
            )

            heartbeat_shutdown_event = threading.Event()
            heartbeat_thread = threading.Thread(
                target=client_heartbeat_thread,
                args=(client, heartbeat_shutdown_event),
                daemon=True,
            )
            heartbeat_thread.start()

            pid = server_process.pid

            self._logger.info(
                f"Created new code server (pid {pid}) for {deployment_name}:{location_name}"
            )

            self._process_entries[server_process.pid] = ProcessUserCodeEntry(
                server_process,
                client,
                heartbeat_shutdown_event,
                heartbeat_thread,
            )

            self._active_pids[key].add(pid)

        endpoint = ServerEndpoint(
            host="localhost",
            port=port,
            socket=socket,
        )

        return DagsterCloudGrpcServer(pid, endpoint, metadata)

    async def _wait_for_new_server_ready(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
        server_handle: int,
        server_endpoint: ServerEndpoint,
    ) -> None:
        await self._wait_for_dagster_server_process(
            client=server_endpoint.create_client(),
            timeout=self._server_process_startup_timeout,
        )

    def _get_standalone_dagster_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> Collection[int]:
        return self._active_pids.get((deployment_name, location_name), set()).copy()

    def _get_multipex_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> Collection[int]:
        return self._active_multipex_pids.get((deployment_name, location_name), set()).copy()

    def _remove_server_handle(self, server_handle: int) -> None:
        pid = server_handle
        process_entry = self._process_entries[pid]
        self._remove_pid(pid)
        if self._wait_for_processes:
            if isinstance(process_entry, ProcessUserCodeEntry):
                try:
                    process_entry.grpc_client.shutdown_server()
                except DagsterUserCodeUnreachableError:
                    # Server already shutdown
                    pass
            else:
                process_entry.grpc_server_process.terminate()

            if process_entry.grpc_server_process.poll() is None:
                process_entry.grpc_server_process.communicate(timeout=30)

    def _remove_pid(self, pid):
        if pid in self._process_entries:
            process_entry = self._process_entries[pid]
            if isinstance(process_entry, ProcessUserCodeEntry):
                # Rely on heartbeat failure to eventually kill the process
                process_entry.heartbeat_shutdown_event.set()
                process_entry.heartbeat_thread.join()
            else:
                # multi-pex server processes don't yet have heartbeats, so just terminate
                # the multipex server process directly.
                process_entry.grpc_server_process.terminate()

            del self._process_entries[pid]

        for pids in self._active_pids.values():
            if pid in pids:
                pids.remove(pid)

        for pids in self._active_multipex_pids.values():
            if pid in pids:
                pids.remove(pid)

    def run_launcher(self) -> CloudProcessRunLauncher:
        if not self._run_launcher:
            self._run_launcher = CloudProcessRunLauncher()
            self._run_launcher.register_instance(self._instance)

        return self._run_launcher

    def _list_server_handles(self) -> list[int]:
        return list(self._process_entries.keys())

    def get_agent_id_for_server(self, handle: int) -> str | None:
        return self._instance.instance_uuid

    def get_server_create_timestamp(self, handle: int) -> float | None:
        return None

    def __exit__(self, exception_type, exception_value, traceback):
        super().__exit__(exception_value, exception_value, traceback)

        if self._cleanup_zombies_thread:
            self._cleanup_zombies_shutdown_event.set()
            self._cleanup_zombies_thread.join()
