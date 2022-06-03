import datetime
import threading
from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Union, cast

import dagster._check as check
from dagster.api.get_server_id import sync_get_server_id
from dagster.api.list_repositories import sync_list_repositories_grpc
from dagster.api.notebook_data import sync_get_streaming_external_notebook_data_grpc
from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster.api.snapshot_partition import (
    sync_get_external_partition_config_grpc,
    sync_get_external_partition_names_grpc,
    sync_get_external_partition_set_execution_param_data_grpc,
    sync_get_external_partition_tags_grpc,
)
from dagster.api.snapshot_pipeline import sync_get_external_pipeline_subset_grpc
from dagster.api.snapshot_repository import sync_get_streaming_external_repositories_data_grpc
from dagster.api.snapshot_schedule import sync_get_external_schedule_execution_data_grpc
from dagster.api.snapshot_sensor import sync_get_external_sensor_execution_data_grpc
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstruct import ReconstructablePipeline
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation import ExternalPipelineSubsetResult
from dagster.core.host_representation.external import (
    ExternalExecutionPlan,
    ExternalPipeline,
    ExternalRepository,
)
from dagster.core.host_representation.grpc_server_registry import GrpcServerRegistry
from dagster.core.host_representation.handle import PipelineHandle, RepositoryHandle
from dagster.core.host_representation.origin import (
    GrpcServerRepositoryLocationOrigin,
    InProcessRepositoryLocationOrigin,
    RepositoryLocationOrigin,
)
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryPythonOrigin
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster.grpc.impl import (
    get_external_schedule_execution,
    get_external_sensor_execution,
    get_notebook_data,
    get_partition_config,
    get_partition_names,
    get_partition_set_execution_param_data,
    get_partition_tags,
)
from dagster.grpc.types import GetCurrentImageResult
from dagster.serdes import deserialize_as
from dagster.seven.compat.pendulum import PendulumDateTime
from dagster.utils import merge_dicts
from dagster.utils.hosted_user_process import external_repo_from_def

from .selector import PipelineSelector

if TYPE_CHECKING:
    from dagster.core.definitions.schedule_definition import ScheduleExecutionData
    from dagster.core.definitions.sensor_definition import SensorExecutionData
    from dagster.core.host_representation import (
        ExternalPartitionConfigData,
        ExternalPartitionExecutionErrorData,
        ExternalPartitionNamesData,
        ExternalPartitionSetExecutionParamData,
        ExternalPartitionTagsData,
        ExternalScheduleExecutionErrorData,
    )
    from dagster.core.host_representation.external_data import ExternalSensorExecutionErrorData


class RepositoryLocation(AbstractContextManager):
    """
    A RepositoryLocation represents a target containing user code which has a set of Dagster
    definition objects. A given location will contain some number of uniquely named
    RepositoryDefinitions, which therein contains Pipeline, Solid, and other definitions.

    Dagster tools are typically "host" processes, meaning they load a RepositoryLocation and
    communicate with it over an IPC/RPC layer. Currently this IPC layer is implemented by
    invoking the dagster CLI in a target python interpreter (e.g. a virtual environment) in either
      a) the current node
      b) a container

    In the near future, we may also make this communication channel able over an RPC layer, in
    which case the information needed to load a RepositoryLocation will be a url that abides by
    some RPC contract.

    We also allow for InProcessRepositoryLocation which actually loads the user-defined artifacts
    into process with the host tool. This is mostly for test scenarios.
    """

    @abstractmethod
    def get_repository(self, name: str) -> ExternalRepository:
        pass

    @abstractmethod
    def has_repository(self, name: str) -> bool:
        pass

    @abstractmethod
    def get_repositories(self) -> Dict[str, ExternalRepository]:
        pass

    def get_repository_names(self) -> List[str]:
        return list(self.get_repositories().keys())

    @property
    def name(self) -> str:
        return self.origin.location_name

    @abstractmethod
    def get_external_execution_plan(
        self,
        external_pipeline: ExternalPipeline,
        run_config: Mapping[str, object],
        mode: str,
        step_keys_to_execute: Optional[List[str]],
        known_state: Optional[KnownExecutionState],
        instance: Optional[DagsterInstance] = None,
    ) -> ExternalExecutionPlan:
        pass

    def get_external_pipeline(self, selector: PipelineSelector) -> ExternalPipeline:
        """Return the ExternalPipeline for a specific pipeline. Subclasses only
        need to implement get_subset_external_pipeline_result to handle the case where
        a solid selection is specified, which requires access to the underlying PipelineDefinition
        to generate the subsetted pipeline snapshot."""
        if not selector.solid_selection and not selector.asset_selection:
            return self.get_repository(selector.repository_name).get_full_external_pipeline(
                selector.pipeline_name
            )

        repo_handle = self.get_repository(selector.repository_name).handle

        return ExternalPipeline(
            self.get_subset_external_pipeline_result(selector).external_pipeline_data, repo_handle
        )

    @abstractmethod
    def get_subset_external_pipeline_result(
        self, selector: PipelineSelector
    ) -> ExternalPipelineSubsetResult:
        """Returns a snapshot about an ExternalPipeline with a solid selection, which requires
        access to the underlying PipelineDefinition. Callsites should likely use
        `get_external_pipeline` instead."""

    @abstractmethod
    def get_external_partition_config(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_partition_tags(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_partition_names(
        self, repository_handle: RepositoryHandle, partition_set_name: str
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: List[str],
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_schedule_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        schedule_name: str,
        scheduled_execution_time,
    ) -> Union["ScheduleExecutionData", "ExternalScheduleExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_sensor_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        name: str,
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
    ) -> Union["SensorExecutionData", "ExternalSensorExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_notebook_data(self, notebook_path: str) -> bytes:
        pass

    @property
    @abstractmethod
    def is_reload_supported(self) -> bool:
        pass

    def __del__(self):
        self.cleanup()

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.cleanup()

    def cleanup(self) -> None:
        pass

    @property
    @abstractmethod
    def origin(self) -> RepositoryLocationOrigin:
        pass

    def get_display_metadata(self) -> Dict[str, str]:
        return merge_dicts(
            self.origin.get_display_metadata(),
            ({"image": self.container_image} if self.container_image else {}),
        )

    @property
    @abstractmethod
    def executable_path(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def container_image(self) -> Optional[str]:
        pass

    @property
    def container_context(self) -> Optional[Dict[str, Any]]:
        return None

    @property
    @abstractmethod
    def entry_point(self) -> Optional[List[str]]:
        pass

    @property
    @abstractmethod
    def repository_code_pointer_dict(self) -> Dict[str, CodePointer]:
        pass

    def get_repository_python_origin(self, repository_name: str) -> "RepositoryPythonOrigin":
        if repository_name not in self.repository_code_pointer_dict:
            raise DagsterInvariantViolationError(
                "Unable to find repository {}.".format(repository_name)
            )

        code_pointer = self.repository_code_pointer_dict[repository_name]
        return RepositoryPythonOrigin(
            executable_path=self.executable_path,
            code_pointer=code_pointer,
            container_image=self.container_image,
            entry_point=self.entry_point,
            container_context=self.container_context,
        )


class InProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, origin: InProcessRepositoryLocationOrigin):
        from dagster.grpc.server import LoadedRepositories

        self._origin = check.inst_param(origin, "origin", InProcessRepositoryLocationOrigin)

        loadable_target_origin = self._origin.loadable_target_origin
        self._loaded_repositories = LoadedRepositories(
            loadable_target_origin,
            self._origin.entry_point,
            self._origin.container_image,
        )

        self._repository_code_pointer_dict = self._loaded_repositories.code_pointers_by_repo_name

        self._recon_repos = {
            repo_name: self._loaded_repositories.get_recon_repo(repo_name)
            for repo_name in self._repository_code_pointer_dict
        }

        self._repositories = {}
        for repo_name in self._repository_code_pointer_dict:
            recon_repo = self._loaded_repositories.get_recon_repo(repo_name)
            repo_def = recon_repo.get_definition()
            self._repositories[repo_name] = external_repo_from_def(
                repo_def,
                RepositoryHandle(repository_name=repo_name, repository_location=self),
            )

    @property
    def is_reload_supported(self) -> bool:
        return False

    @property
    def origin(self) -> InProcessRepositoryLocationOrigin:
        return self._origin

    @property
    def executable_path(self) -> Optional[str]:
        return self._origin.loadable_target_origin.executable_path

    @property
    def container_image(self) -> Optional[str]:
        return self._origin.container_image

    @property
    def container_context(self) -> Optional[Dict[str, Any]]:
        return self._origin.container_context

    @property
    def entry_point(self) -> Optional[List[str]]:
        return self._origin.entry_point

    @property
    def repository_code_pointer_dict(self) -> Dict[str, CodePointer]:
        return self._repository_code_pointer_dict

    def get_reconstructable_pipeline(self, name: str) -> ReconstructablePipeline:
        return self._recon_repos[name].get_reconstructable_pipeline(name)

    def get_repository(self, name: str) -> ExternalRepository:
        return self._repositories[name]

    def has_repository(self, name: str) -> bool:
        return name in self._repositories

    def get_repositories(self) -> Dict[str, ExternalRepository]:
        return self._repositories

    def get_subset_external_pipeline_result(
        self, selector: PipelineSelector
    ) -> ExternalPipelineSubsetResult:
        check.inst_param(selector, "selector", PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            "PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}".format(
                self=self, selector=selector
            ),
        )

        from dagster.grpc.impl import get_external_pipeline_subset_result

        return get_external_pipeline_subset_result(
            self.get_reconstructable_pipeline(selector.pipeline_name),
            selector.solid_selection,
            selector.asset_selection,
        )

    def get_external_execution_plan(
        self,
        external_pipeline: ExternalPipeline,
        run_config: Mapping[str, object],
        mode: str,
        step_keys_to_execute: Optional[List[str]],
        known_state: Optional[KnownExecutionState],
        instance: Optional[DagsterInstance] = None,
    ) -> ExternalExecutionPlan:
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.dict_param(run_config, "run_config")
        check.str_param(mode, "mode")
        check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)
        check.opt_inst_param(instance, "instance", DagsterInstance)

        execution_plan = create_execution_plan(
            pipeline=self.get_reconstructable_pipeline(
                external_pipeline.name
            ).subset_for_execution_from_existing_pipeline(
                external_pipeline.solids_to_execute, external_pipeline.asset_selection
            ),
            run_config=run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
        )
        return ExternalExecutionPlan(
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan,
                external_pipeline.identifying_pipeline_snapshot_id,
            )
        )

    def get_external_partition_config(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_config(
            recon_repo=self._recon_repos[repository_handle.repository_name],
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_tags(
            recon_repo=self._recon_repos[repository_handle.repository_name],
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(
        self, repository_handle: RepositoryHandle, partition_set_name: str
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")

        return get_partition_names(
            recon_repo=self._recon_repos[repository_handle.repository_name],
            partition_set_name=partition_set_name,
        )

    def get_external_schedule_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        schedule_name: str,
        scheduled_execution_time,
    ) -> Union["ScheduleExecutionData", "ExternalScheduleExecutionErrorData"]:
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(scheduled_execution_time, "scheduled_execution_time", PendulumDateTime)

        return get_external_schedule_execution(
            recon_repo=self._recon_repos[repository_handle.repository_name],
            instance_ref=instance.get_ref(),
            schedule_name=schedule_name,
            scheduled_execution_timestamp=scheduled_execution_time.timestamp()
            if scheduled_execution_time
            else None,
            scheduled_execution_timezone=scheduled_execution_time.timezone.name
            if scheduled_execution_time
            else None,
        )

    def get_external_sensor_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        name: str,
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
    ) -> Union["SensorExecutionData", "ExternalSensorExecutionErrorData"]:
        return get_external_sensor_execution(
            self._recon_repos[repository_handle.repository_name],
            instance.get_ref(),
            name,
            last_completion_time,
            last_run_key,
            cursor,
        )

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: List[str],
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.list_param(partition_names, "partition_names", of_type=str)

        return get_partition_set_execution_param_data(
            recon_repo=self._recon_repos[repository_handle.repository_name],
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )

    def get_external_notebook_data(self, notebook_path: str) -> bytes:
        check.str_param(notebook_path, "notebook_path")
        return get_notebook_data(notebook_path)


class GrpcServerRepositoryLocation(RepositoryLocation):
    def __init__(
        self,
        origin: RepositoryLocationOrigin,
        host: Optional[str] = None,
        port: Optional[int] = None,
        socket: Optional[str] = None,
        server_id: Optional[str] = None,
        heartbeat: Optional[bool] = False,
        watch_server: Optional[bool] = True,
        grpc_server_registry: Optional[GrpcServerRegistry] = None,
    ):
        from dagster.grpc.client import DagsterGrpcClient, client_heartbeat_thread

        self._origin = check.inst_param(origin, "origin", RepositoryLocationOrigin)

        self.grpc_server_registry = check.opt_inst_param(
            grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
        )

        if isinstance(self.origin, GrpcServerRepositoryLocationOrigin):
            self._port = self.origin.port
            self._socket = self.origin.socket
            self._host = self.origin.host
            self._use_ssl = bool(self.origin.use_ssl)
        else:
            self._port = check.opt_int_param(port, "port")
            self._socket = check.opt_str_param(socket, "socket")
            self._host = check.str_param(host, "host")
            self._use_ssl = False

        self._watch_thread_shutdown_event = None
        self._watch_thread = None

        self._heartbeat_shutdown_event = None
        self._heartbeat_thread = None

        self._heartbeat = check.bool_param(heartbeat, "heartbeat")
        self._watch_server = check.bool_param(watch_server, "watch_server")

        self.server_id = None
        self._external_repositories_data = None

        self._executable_path = None
        self._container_image = None
        self._container_context = None
        self._repository_code_pointer_dict = None
        self._entry_point = None

        try:
            self.client = DagsterGrpcClient(
                port=self._port,
                socket=self._socket,
                host=self._host,
                use_ssl=self._use_ssl,
            )
            list_repositories_response = sync_list_repositories_grpc(self.client)

            self.server_id = server_id if server_id else sync_get_server_id(self.client)
            self.repository_names = set(
                symbol.repository_name for symbol in list_repositories_response.repository_symbols
            )

            if self._heartbeat:
                self._heartbeat_shutdown_event = threading.Event()

                self._heartbeat_thread = threading.Thread(
                    target=client_heartbeat_thread,
                    args=(
                        self.client,
                        self._heartbeat_shutdown_event,
                    ),
                    name="grpc-client-heartbeat",
                )
                self._heartbeat_thread.daemon = True
                self._heartbeat_thread.start()

            self._executable_path = list_repositories_response.executable_path
            self._repository_code_pointer_dict = (
                list_repositories_response.repository_code_pointer_dict
            )
            self._entry_point = list_repositories_response.entry_point

            self._container_image = (
                list_repositories_response.container_image
                or self._reload_current_image()  # Back-compat for older gRPC servers that did not include container_image in ListRepositoriesResponse
            )

            self._container_context = list_repositories_response.container_context

            self._external_repositories_data = sync_get_streaming_external_repositories_data_grpc(
                self.client,
                self,
            )

            self.external_repositories = {
                repo_name: ExternalRepository(
                    repo_data,
                    RepositoryHandle(
                        repository_name=repo_name,
                        repository_location=self,
                    ),
                )
                for repo_name, repo_data in self._external_repositories_data.items()
            }
        except:
            self.cleanup()
            raise

    @property
    def origin(self) -> RepositoryLocationOrigin:
        return self._origin

    @property
    def container_image(self) -> str:
        return cast(str, self._container_image)

    @property
    def container_context(self) -> Optional[Dict[str, Any]]:
        return self._container_context

    @property
    def repository_code_pointer_dict(self) -> Dict[str, CodePointer]:
        return cast(Dict[str, CodePointer], self._repository_code_pointer_dict)

    @property
    def executable_path(self) -> Optional[str]:
        return self._executable_path

    @property
    def entry_point(self) -> Optional[List[str]]:
        return self._entry_point

    @property
    def port(self) -> Optional[int]:
        return self._port

    @property
    def socket(self) -> Optional[str]:
        return self._socket

    @property
    def host(self) -> str:
        return self._host

    @property
    def use_ssl(self) -> bool:
        return self._use_ssl

    def _reload_current_image(self) -> Optional[str]:
        return deserialize_as(
            self.client.get_current_image(),
            GetCurrentImageResult,
        ).current_image

    def cleanup(self) -> None:
        if self._heartbeat_shutdown_event:
            self._heartbeat_shutdown_event.set()
            self._heartbeat_shutdown_event = None

        if self._watch_thread_shutdown_event:
            self._watch_thread_shutdown_event.set()
            self._watch_thread_shutdown_event = None

        if self._heartbeat_thread:
            self._heartbeat_thread.join()
            self._heartbeat_thread = None

        if self._watch_thread:
            self._watch_thread.join()
            self._watch_thread = None

    @property
    def is_reload_supported(self) -> bool:
        return True

    def get_repository(self, name: str) -> ExternalRepository:
        check.str_param(name, "name")
        return self.get_repositories()[name]

    def has_repository(self, name: str) -> bool:
        return name in self.get_repositories()

    def get_repositories(self) -> Dict[str, ExternalRepository]:
        return self.external_repositories

    def get_external_execution_plan(
        self,
        external_pipeline: ExternalPipeline,
        run_config: Mapping[str, Any],
        mode: str,
        step_keys_to_execute: Optional[List[str]],
        known_state: Optional[KnownExecutionState],
        instance: Optional[DagsterInstance] = None,
    ) -> ExternalExecutionPlan:
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        run_config = check.dict_param(run_config, "run_config")
        check.str_param(mode, "mode")
        check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)
        check.opt_inst_param(instance, "instance", DagsterInstance)

        execution_plan_snapshot_or_error = sync_get_external_execution_plan_grpc(
            api_client=self.client,
            pipeline_origin=external_pipeline.get_external_origin(),
            run_config=run_config,
            mode=mode,
            pipeline_snapshot_id=external_pipeline.identifying_pipeline_snapshot_id,
            asset_selection=external_pipeline.asset_selection,
            solid_selection=external_pipeline.solid_selection,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=instance,
        )

        return ExternalExecutionPlan(execution_plan_snapshot=execution_plan_snapshot_or_error)

    def get_subset_external_pipeline_result(
        self, selector: PipelineSelector
    ) -> "ExternalPipelineSubsetResult":
        check.inst_param(selector, "selector", PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            "PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}".format(
                self=self, selector=selector
            ),
        )

        external_repository = self.get_repository(selector.repository_name)
        pipeline_handle = PipelineHandle(selector.pipeline_name, external_repository.handle)
        return sync_get_external_pipeline_subset_grpc(
            self.client,
            pipeline_handle.get_external_origin(),
            selector.solid_selection,
            selector.asset_selection,
        )

    def get_external_partition_config(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> "ExternalPartitionConfigData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_config_grpc(
            self.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_tags(
        self, repository_handle: RepositoryHandle, partition_set_name: str, partition_name: str
    ) -> "ExternalPartitionTagsData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_tags_grpc(
            self.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_names(
        self, repository_handle: RepositoryHandle, partition_set_name: str
    ) -> "ExternalPartitionNamesData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")

        return sync_get_external_partition_names_grpc(
            self.client, repository_handle, partition_set_name
        )

    def get_external_schedule_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        schedule_name: str,
        scheduled_execution_time: Optional[datetime.datetime],
    ) -> "ScheduleExecutionData":
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(scheduled_execution_time, "scheduled_execution_time", PendulumDateTime)

        return sync_get_external_schedule_execution_data_grpc(
            self.client,
            instance,
            repository_handle,
            schedule_name,
            scheduled_execution_time,
        )

    def get_external_sensor_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        name: str,
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
    ) -> "SensorExecutionData":
        return sync_get_external_sensor_execution_data_grpc(
            self.client,
            instance,
            repository_handle,
            name,
            last_completion_time,
            last_run_key,
            cursor,
        )

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: List[str],
    ) -> "ExternalPartitionSetExecutionParamData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.list_param(partition_names, "partition_names", of_type=str)

        return sync_get_external_partition_set_execution_param_data_grpc(
            self.client, repository_handle, partition_set_name, partition_names
        )

    def get_external_notebook_data(self, notebook_path: str) -> bytes:
        check.str_param(notebook_path, "notebook_path")
        return sync_get_streaming_external_notebook_data_grpc(self.client, notebook_path)
