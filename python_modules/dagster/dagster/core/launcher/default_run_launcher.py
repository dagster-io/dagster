import time
import weakref

import grpc
from dagster import check, seven
from dagster.core.errors import DagsterLaunchFailedError
from dagster.core.host_representation import ExternalPipeline
from dagster.core.host_representation.handle import (
    GrpcServerRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.tags import GRPC_INFO_TAG
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.types import (
    CanCancelExecutionRequest,
    CancelExecutionRequest,
    ExecuteExternalPipelineArgs,
)
from dagster.serdes import ConfigurableClass
from dagster.utils import merge_dicts

from .base import RunLauncher

GRPC_REPOSITORY_LOCATION_HANDLE_TYPES = (
    GrpcServerRepositoryLocationHandle,
    ManagedGrpcPythonEnvRepositoryLocationHandle,
)


class DefaultRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs against running GRPC servers."""

    def __init__(self, inst_data=None):
        self._instance_weakref = None
        self._inst_data = inst_data

        # Used for test cleanup purposes only
        self._run_id_to_repository_location_handle_cache = {}

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return DefaultRunLauncher(inst_data=inst_data)

    @property
    def _instance(self):
        return self._instance_weakref() if self._instance_weakref else None

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)
        check.invariant(self._instance is None, "Must only call initialize once")
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_weakref = weakref.ref(instance)

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(run, "run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)

        repository_location_handle = external_pipeline.repository_handle.repository_location_handle

        check.inst(
            repository_location_handle,
            GRPC_REPOSITORY_LOCATION_HANDLE_TYPES,
            "DefaultRunLauncher: Can't launch runs for pipeline not loaded from a GRPC server",
        )

        self._instance.add_run_tags(
            run.run_id,
            {
                GRPC_INFO_TAG: seven.json.dumps(
                    merge_dicts(
                        {"host": repository_location_handle.host},
                        {"port": repository_location_handle.port}
                        if repository_location_handle.port
                        else {"socket": repository_location_handle.socket},
                    )
                )
            },
        )

        res = repository_location_handle.client.start_run(
            ExecuteExternalPipelineArgs(
                pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )

        if not res.success:
            raise (
                DagsterLaunchFailedError(
                    res.message, serializable_error_info=res.serializable_error_info
                )
            )

        self._run_id_to_repository_location_handle_cache[run.run_id] = repository_location_handle

        return run

    def _get_grpc_client_for_termination(self, run_id):
        if not self._instance:
            return None

        run = self._instance.get_run_by_id(run_id)
        if not run or run.is_finished:
            return None

        tags = run.tags

        if GRPC_INFO_TAG not in tags:
            return None

        grpc_info = seven.json.loads(tags.get(GRPC_INFO_TAG))

        return DagsterGrpcClient(
            port=grpc_info.get("port"), socket=grpc_info.get("socket"), host=grpc_info.get("host")
        )

    def can_terminate(self, run_id):
        check.str_param(run_id, "run_id")

        client = self._get_grpc_client_for_termination(run_id)
        if not client:
            return False

        try:
            res = client.can_cancel_execution(CanCancelExecutionRequest(run_id=run_id), timeout=5)
        except grpc._channel._InactiveRpcError:  # pylint: disable=protected-access
            # Server that created the run may no longer exist
            return False

        return res.can_cancel

    def terminate(self, run_id):
        check.str_param(run_id, "run_id")
        if not self._instance:
            return False

        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False

        client = self._get_grpc_client_for_termination(run_id)

        if not client:
            self._instance.report_engine_event(
                message="Unable to get grpc client to send termination request to.",
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        self._instance.report_run_canceling(run)
        res = client.cancel_execution(CancelExecutionRequest(run_id=run_id))
        return res.success

    def join(self, timeout=30):
        # If this hasn't been initialized at all, we can just do a noop
        if not self._instance:
            return

        total_time = 0
        interval = 0.01

        while True:
            active_run_ids = [
                run_id
                for run_id in self._run_id_to_repository_location_handle_cache.keys()
                if (
                    self._instance.get_run_by_id(run_id)
                    and not self._instance.get_run_by_id(run_id).is_finished
                )
            ]

            if len(active_run_ids) == 0:
                return

            if total_time >= timeout:
                raise Exception(
                    "Timed out waiting for these runs to finish: {active_run_ids}".format(
                        active_run_ids=repr(active_run_ids)
                    )
                )

            total_time += interval
            time.sleep(interval)
            interval = interval * 2

    def cleanup_managed_grpc_servers(self):
        """Shut down any managed grpc servers that used this run launcher to start a run.
        Should only be used for teardown purposes within tests (generally it's fine for a server
        to out-live the host process, since it might be finishing an execution and will
        automatically shut itself down once it no longer receives a heartbeat from the host
        process). But in tests, gRPC servers access the DagsterInstance during execution, so we need
        to shut them down before we can safely remove the temporary directory created for the
        DagsterInstance.
        """
        for repository_location_handle in self._run_id_to_repository_location_handle_cache.values():
            if isinstance(repository_location_handle, ManagedGrpcPythonEnvRepositoryLocationHandle):
                check.invariant(
                    repository_location_handle.is_cleaned_up,
                    "ManagedGrpcPythonRepositoryLocationHandle was not cleaned up "
                    "before test teardown. This may indicate that the handle is not "
                    "being used as a contextmanager.",
                )
                repository_location_handle.grpc_server_process.wait()
