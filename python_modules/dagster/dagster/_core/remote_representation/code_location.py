import datetime
import sys
import threading
from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Tuple, Union, cast

import dagster._check as check
from dagster._api.get_server_id import sync_get_server_id
from dagster._api.list_repositories import sync_list_repositories_grpc
from dagster._api.notebook_data import sync_get_streaming_external_notebook_data_grpc
from dagster._api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster._api.snapshot_job import sync_get_external_job_subset_grpc
from dagster._api.snapshot_partition import (
    sync_get_external_partition_config_grpc,
    sync_get_external_partition_names_grpc,
    sync_get_external_partition_set_execution_param_data_grpc,
    sync_get_external_partition_tags_grpc,
)
from dagster._api.snapshot_repository import sync_get_streaming_external_repositories_data_grpc
from dagster._api.snapshot_schedule import sync_get_external_schedule_execution_data_grpc
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import (
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
    DagsterUserCodeProcessError,
)
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance
from dagster._core.libraries import DagsterLibraryRegistry
from dagster._core.origin import RepositoryPythonOrigin
from dagster._core.remote_representation import ExternalJobSubsetResult
from dagster._core.remote_representation.external import (
    ExternalExecutionPlan,
    ExternalJob,
    ExternalPartitionSet,
    ExternalRepository,
)
from dagster._core.remote_representation.external_data import (
    ExternalPartitionNamesData,
    ExternalScheduleExecutionErrorData,
    ExternalSensorExecutionErrorData,
    external_partition_set_name_for_job_name,
    external_repository_data_from_def,
)
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.remote_representation.handle import JobHandle, RepositoryHandle
from dagster._core.remote_representation.origin import (
    CodeLocationOrigin,
    GrpcServerCodeLocationOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster._grpc.impl import (
    get_external_schedule_execution,
    get_external_sensor_execution,
    get_notebook_data,
    get_partition_config,
    get_partition_names,
    get_partition_set_execution_param_data,
    get_partition_tags,
)
from dagster._grpc.types import GetCurrentImageResult, GetCurrentRunsResult
from dagster._serdes import deserialize_value
from dagster._seven.compat.pendulum import PendulumDateTime
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.definitions.schedule_definition import ScheduleExecutionData
    from dagster._core.definitions.sensor_definition import SensorExecutionData
    from dagster._core.remote_representation import (
        ExternalPartitionConfigData,
        ExternalPartitionExecutionErrorData,
        ExternalPartitionSetExecutionParamData,
        ExternalPartitionTagsData,
    )


class CodeLocation(AbstractContextManager):
    """A CodeLocation represents a target containing user code which has a set of Dagster
    definition objects. A given location will contain some number of uniquely named
    RepositoryDefinitions, which therein contains job, op, and other definitions.

    Dagster tools are typically "host" processes, meaning they load a CodeLocation and
    communicate with it over an IPC/RPC layer. Currently this IPC layer is implemented by
    invoking the dagster CLI in a target python interpreter (e.g. a virtual environment) in either
      a) the current node
      b) a container

    In the near future, we may also make this communication channel able over an RPC layer, in
    which case the information needed to load a CodeLocation will be a url that abides by
    some RPC contract.

    We also allow for InProcessCodeLocation which actually loads the user-defined artifacts
    into process with the host tool. This is mostly for test scenarios.
    """

    @abstractmethod
    def get_repository(self, name: str) -> ExternalRepository:
        pass

    @abstractmethod
    def has_repository(self, name: str) -> bool:
        pass

    @abstractmethod
    def get_repositories(self) -> Mapping[str, ExternalRepository]:
        pass

    def get_repository_names(self) -> Sequence[str]:
        return list(self.get_repositories().keys())

    @property
    def name(self) -> str:
        return self.origin.location_name

    @abstractmethod
    def get_external_execution_plan(
        self,
        external_job: ExternalJob,
        run_config: Mapping[str, object],
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: Optional[KnownExecutionState],
        instance: Optional[DagsterInstance] = None,
    ) -> ExternalExecutionPlan:
        pass

    def get_external_job(self, selector: JobSubsetSelector) -> ExternalJob:
        """Return the ExternalPipeline for a specific pipeline. Subclasses only
        need to implement get_subset_external_pipeline_result to handle the case where
        an op selection is specified, which requires access to the underlying JobDefinition
        to generate the subsetted pipeline snapshot.
        """
        if (
            not selector.op_selection
            and not selector.asset_selection
            and not selector.asset_check_selection
        ):
            return self.get_repository(selector.repository_name).get_full_external_job(
                selector.job_name
            )

        repo_handle = self.get_repository(selector.repository_name).handle

        subset_result = self.get_subset_external_job_result(selector)
        external_data = subset_result.external_job_data
        if external_data is None:
            error = check.not_none(subset_result.error)
            if error.cls_name == "DagsterInvalidSubsetError":
                raise DagsterInvalidSubsetError(check.not_none(error.message))
            else:
                check.failed(
                    f"Failed to fetch subset data, success: {subset_result.success} error:"
                    f" {error}"
                )

        return ExternalJob(external_data, repo_handle)

    @abstractmethod
    def get_subset_external_job_result(
        self, selector: JobSubsetSelector
    ) -> ExternalJobSubsetResult:
        """Returns a snapshot about an ExternalPipeline with an op selection, which requires
        access to the underlying JobDefinition. Callsites should likely use
        `get_external_pipeline` instead.
        """

    @abstractmethod
    def get_external_partition_config(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_partition_tags(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_partition_names(
        self, external_partition_set: ExternalPartitionSet, instance: DagsterInstance
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: Sequence[str],
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        pass

    @abstractmethod
    def get_external_schedule_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        schedule_name: str,
        scheduled_execution_time: datetime.datetime,
        log_key: Optional[Sequence[str]],
    ) -> "ScheduleExecutionData":
        pass

    @abstractmethod
    def get_external_sensor_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        name: str,
        last_tick_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
        log_key: Optional[Sequence[str]],
        last_sensor_start_time: Optional[float],
    ) -> "SensorExecutionData":
        pass

    def get_asset_job_partitions_def(
        self, external_job: ExternalJob
    ) -> Optional[PartitionsDefinition]:
        external_repository_data = self.get_repository(
            external_job.repository_handle.repository_name
        ).external_repository_data
        external_partition_set_name = external_partition_set_name_for_job_name(external_job.name)

        if external_repository_data.has_external_partition_set_data(external_partition_set_name):
            external_partitions_def_data = external_repository_data.get_external_partition_set_data(
                external_partition_set_name
            ).external_partitions_data
            return (
                external_partitions_def_data.get_partitions_definition()
                if external_partitions_def_data
                else None
            )

        return None

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
    def origin(self) -> CodeLocationOrigin:
        pass

    def get_display_metadata(self) -> Mapping[str, str]:
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
    def container_context(self) -> Optional[Mapping[str, Any]]:
        return None

    @property
    @abstractmethod
    def entry_point(self) -> Optional[Sequence[str]]:
        pass

    @property
    @abstractmethod
    def repository_code_pointer_dict(self) -> Mapping[str, CodePointer]:
        pass

    def get_repository_python_origin(self, repository_name: str) -> "RepositoryPythonOrigin":
        if repository_name not in self.repository_code_pointer_dict:
            raise DagsterInvariantViolationError(f"Unable to find repository {repository_name}.")

        code_pointer = self.repository_code_pointer_dict[repository_name]
        return RepositoryPythonOrigin(
            executable_path=self.executable_path or sys.executable,
            code_pointer=code_pointer,
            container_image=self.container_image,
            entry_point=self.entry_point,
            container_context=self.container_context,
        )

    @abstractmethod
    def get_dagster_library_versions(self) -> Optional[Mapping[str, str]]: ...


class InProcessCodeLocation(CodeLocation):
    def __init__(self, origin: InProcessCodeLocationOrigin, instance: DagsterInstance):
        from dagster._grpc.server import LoadedRepositories

        self._origin = check.inst_param(origin, "origin", InProcessCodeLocationOrigin)
        self._instance = instance

        loadable_target_origin = self._origin.loadable_target_origin
        self._loaded_repositories = LoadedRepositories(
            loadable_target_origin,
            self._origin.entry_point,
            self._origin.container_image,
        )

        self._repository_code_pointer_dict = self._loaded_repositories.code_pointers_by_repo_name

        self._repositories: Dict[str, ExternalRepository] = {}
        for repo_name, repo_def in self._loaded_repositories.definitions_by_name.items():
            self._repositories[repo_name] = ExternalRepository(
                external_repository_data_from_def(repo_def),
                RepositoryHandle(repository_name=repo_name, code_location=self),
                instance=instance,
            )

    @property
    def is_reload_supported(self) -> bool:
        return False

    @property
    def origin(self) -> InProcessCodeLocationOrigin:
        return self._origin

    @property
    def executable_path(self) -> Optional[str]:
        return self._origin.loadable_target_origin.executable_path

    @property
    def container_image(self) -> Optional[str]:
        return self._origin.container_image

    @property
    def container_context(self) -> Optional[Mapping[str, Any]]:
        return self._origin.container_context

    @property
    def entry_point(self) -> Optional[Sequence[str]]:
        return self._origin.entry_point

    @property
    def repository_code_pointer_dict(self) -> Mapping[str, CodePointer]:
        return self._repository_code_pointer_dict

    def get_reconstructable_job(self, repository_name: str, name: str) -> ReconstructableJob:
        return self._loaded_repositories.reconstructables_by_name[
            repository_name
        ].get_reconstructable_job(name)

    def _get_repo_def(self, name: str) -> RepositoryDefinition:
        return self._loaded_repositories.definitions_by_name[name]

    def get_repository(self, name: str) -> ExternalRepository:
        return self._repositories[name]

    def has_repository(self, name: str) -> bool:
        return name in self._repositories

    def get_repositories(self) -> Mapping[str, ExternalRepository]:
        return self._repositories

    def get_subset_external_job_result(
        self, selector: JobSubsetSelector
    ) -> ExternalJobSubsetResult:
        check.inst_param(selector, "selector", JobSubsetSelector)
        check.invariant(
            selector.location_name == self.name,
            f"PipelineSelector location_name mismatch, got {selector.location_name} expected"
            f" {self.name}",
        )

        from dagster._grpc.impl import get_external_pipeline_subset_result

        return get_external_pipeline_subset_result(
            self._get_repo_def(selector.repository_name),
            selector.job_name,
            selector.op_selection,
            selector.asset_selection,
            selector.asset_check_selection,
            include_parent_snapshot=True,
        )

    def get_external_execution_plan(
        self,
        external_job: ExternalJob,
        run_config: Mapping[str, object],
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: Optional[KnownExecutionState],
        instance: Optional[DagsterInstance] = None,
    ) -> ExternalExecutionPlan:
        check.inst_param(external_job, "external_job", ExternalJob)
        check.mapping_param(run_config, "run_config")
        step_keys_to_execute = check.opt_nullable_sequence_param(
            step_keys_to_execute, "step_keys_to_execute", of_type=str
        )
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)
        check.opt_inst_param(instance, "instance", DagsterInstance)

        execution_plan = create_execution_plan(
            job=self.get_reconstructable_job(
                external_job.repository_handle.repository_name, external_job.name
            ).get_subset(
                op_selection=external_job.resolved_op_selection,
                asset_selection=external_job.asset_selection,
                asset_check_selection=external_job.asset_check_selection,
            ),
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
        )
        return ExternalExecutionPlan(
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan,
                external_job.identifying_job_snapshot_id,
            )
        )

    def get_external_partition_config(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionConfigData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_config(
            self._get_repo_def(repository_handle.repository_name),
            partition_set_name=partition_set_name,
            partition_key=partition_name,
            instance_ref=instance.get_ref(),
        )

    def get_external_partition_tags(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionTagsData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")
        check.inst_param(instance, "instance", DagsterInstance)

        return get_partition_tags(
            self._get_repo_def(repository_handle.repository_name),
            partition_set_name=partition_set_name,
            partition_name=partition_name,
            instance_ref=instance.get_ref(),
        )

    def get_external_partition_names(
        self, external_partition_set: ExternalPartitionSet, instance: DagsterInstance
    ) -> Union["ExternalPartitionNamesData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(external_partition_set, "external_partition_set", ExternalPartitionSet)

        # Prefer to return the names without calling out to user code if the
        # partition set allows it
        if external_partition_set.has_partition_name_data():
            return ExternalPartitionNamesData(
                partition_names=external_partition_set.get_partition_names(instance)
            )

        return get_partition_names(
            self._get_repo_def(external_partition_set.repository_handle.repository_name),
            partition_set_name=external_partition_set.name,
        )

    def get_external_schedule_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        schedule_name: str,
        scheduled_execution_time: datetime.datetime,  # actually a pendulum datetime
        log_key: Optional[Sequence[str]],
    ) -> "ScheduleExecutionData":
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(scheduled_execution_time, "scheduled_execution_time", PendulumDateTime)
        check.opt_list_param(log_key, "log_key", of_type=str)

        result = get_external_schedule_execution(
            self._get_repo_def(repository_handle.repository_name),
            instance_ref=instance.get_ref(),
            schedule_name=schedule_name,
            scheduled_execution_timestamp=scheduled_execution_time.timestamp(),
            scheduled_execution_timezone=scheduled_execution_time.timezone.name,  # type: ignore
            log_key=log_key,
        )
        if isinstance(result, ExternalScheduleExecutionErrorData):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        return result

    def get_external_sensor_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        name: str,
        last_tick_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
        log_key: Optional[Sequence[str]],
        last_sensor_start_time: Optional[float],
    ) -> "SensorExecutionData":
        result = get_external_sensor_execution(
            self._get_repo_def(repository_handle.repository_name),
            instance.get_ref(),
            name,
            last_tick_completion_time,
            last_run_key,
            cursor,
            log_key,
            last_sensor_start_time,
        )
        if isinstance(result, ExternalSensorExecutionErrorData):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        return result

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: Sequence[str],
        instance: DagsterInstance,
    ) -> Union["ExternalPartitionSetExecutionParamData", "ExternalPartitionExecutionErrorData"]:
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.sequence_param(partition_names, "partition_names", of_type=str)

        return get_partition_set_execution_param_data(
            self._get_repo_def(repository_handle.repository_name),
            partition_set_name=partition_set_name,
            partition_names=partition_names,
            instance_ref=instance.get_ref(),
        )

    def get_external_notebook_data(self, notebook_path: str) -> bytes:
        check.str_param(notebook_path, "notebook_path")
        return get_notebook_data(notebook_path)

    def get_dagster_library_versions(self) -> Mapping[str, str]:
        return DagsterLibraryRegistry.get()


class GrpcServerCodeLocation(CodeLocation):
    def __init__(
        self,
        origin: CodeLocationOrigin,
        instance: DagsterInstance,
        host: Optional[str] = None,
        port: Optional[int] = None,
        socket: Optional[str] = None,
        server_id: Optional[str] = None,
        heartbeat: Optional[bool] = False,
        watch_server: Optional[bool] = True,
        grpc_server_registry: Optional[GrpcServerRegistry] = None,
        grpc_metadata: Optional[Sequence[Tuple[str, str]]] = None,
    ):
        from dagster._grpc.client import DagsterGrpcClient, client_heartbeat_thread

        self._origin = check.inst_param(origin, "origin", CodeLocationOrigin)
        self._instance = instance

        self.grpc_server_registry = check.opt_inst_param(
            grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
        )

        if isinstance(self.origin, GrpcServerCodeLocationOrigin):
            self._port = self.origin.port
            self._socket = self.origin.socket
            self._host = self.origin.host
            self._use_ssl = bool(self.origin.use_ssl)
        else:
            self._port = check.opt_int_param(port, "port")
            self._socket = check.opt_str_param(socket, "socket")
            self._host = check.str_param(host, "host")
            self._use_ssl = False

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
                metadata=grpc_metadata,
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
                    daemon=True,
                )
                self._heartbeat_thread.start()

            self._executable_path = list_repositories_response.executable_path
            self._repository_code_pointer_dict = (
                list_repositories_response.repository_code_pointer_dict
            )
            self._entry_point = list_repositories_response.entry_point
            self._dagster_library_versions = list_repositories_response.dagster_library_versions
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
                        code_location=self,
                    ),
                    instance,
                )
                for repo_name, repo_data in self._external_repositories_data.items()
            }
        except:
            self.cleanup()
            raise

    @property
    def origin(self) -> CodeLocationOrigin:
        return self._origin

    @property
    def container_image(self) -> str:
        return cast(str, self._container_image)

    @property
    def container_context(self) -> Optional[Mapping[str, Any]]:
        return self._container_context

    @property
    def repository_code_pointer_dict(self) -> Mapping[str, CodePointer]:
        return cast(Mapping[str, CodePointer], self._repository_code_pointer_dict)

    @property
    def executable_path(self) -> Optional[str]:
        return self._executable_path

    @property
    def entry_point(self) -> Optional[Sequence[str]]:
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
        return deserialize_value(
            self.client.get_current_image(),
            GetCurrentImageResult,
        ).current_image

    def get_current_runs(self) -> Sequence[str]:
        return deserialize_value(self.client.get_current_runs(), GetCurrentRunsResult).current_runs

    def cleanup(self) -> None:
        if self._heartbeat_shutdown_event:
            self._heartbeat_shutdown_event.set()
            self._heartbeat_shutdown_event = None

        if self._heartbeat_thread:
            self._heartbeat_thread.join()
            self._heartbeat_thread = None

    @property
    def is_reload_supported(self) -> bool:
        return True

    def get_repository(self, name: str) -> ExternalRepository:
        check.str_param(name, "name")
        return self.get_repositories()[name]

    def has_repository(self, name: str) -> bool:
        return name in self.get_repositories()

    def get_repositories(self) -> Mapping[str, ExternalRepository]:
        return self.external_repositories

    def get_external_execution_plan(
        self,
        external_job: ExternalJob,
        run_config: Mapping[str, Any],
        step_keys_to_execute: Optional[Sequence[str]],
        known_state: Optional[KnownExecutionState],
        instance: Optional[DagsterInstance] = None,
    ) -> ExternalExecutionPlan:
        check.inst_param(external_job, "external_job", ExternalJob)
        run_config = check.mapping_param(run_config, "run_config")
        check.opt_nullable_sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)
        check.opt_inst_param(instance, "instance", DagsterInstance)

        asset_selection = (
            frozenset(check.opt_set_param(external_job.asset_selection, "asset_selection"))
            if external_job.asset_selection is not None
            else None
        )
        asset_check_selection = (
            frozenset(
                check.opt_set_param(external_job.asset_check_selection, "asset_check_selection")
            )
            if external_job.asset_check_selection is not None
            else None
        )

        execution_plan_snapshot_or_error = sync_get_external_execution_plan_grpc(
            api_client=self.client,
            job_origin=external_job.get_external_origin(),
            run_config=run_config,
            job_snapshot_id=external_job.identifying_job_snapshot_id,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            op_selection=external_job.op_selection,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=instance,
        )

        return ExternalExecutionPlan(execution_plan_snapshot=execution_plan_snapshot_or_error)

    def get_subset_external_job_result(
        self, selector: JobSubsetSelector
    ) -> "ExternalJobSubsetResult":
        check.inst_param(selector, "selector", JobSubsetSelector)
        check.invariant(
            selector.location_name == self.name,
            f"PipelineSelector location_name mismatch, got {selector.location_name} expected"
            f" {self.name}",
        )

        external_repository = self.get_repository(selector.repository_name)
        job_handle = JobHandle(selector.job_name, external_repository.handle)
        subset = sync_get_external_job_subset_grpc(
            self.client,
            job_handle.get_external_origin(),
            include_parent_snapshot=False,
            op_selection=selector.op_selection,
            asset_selection=selector.asset_selection,
            asset_check_selection=selector.asset_check_selection,
        )
        if subset.external_job_data:
            full_job = self.get_repository(selector.repository_name).get_full_external_job(
                selector.job_name
            )
            subset = subset._replace(
                external_job_data=subset.external_job_data._replace(
                    parent_job_snapshot=full_job.job_snapshot
                )
            )

        return subset

    def get_external_partition_config(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> "ExternalPartitionConfigData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_config_grpc(
            self.client, repository_handle, partition_set_name, partition_name, instance
        )

    def get_external_partition_tags(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_name: str,
        instance: DagsterInstance,
    ) -> "ExternalPartitionTagsData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_tags_grpc(
            self.client, repository_handle, partition_set_name, partition_name, instance
        )

    def get_external_partition_names(
        self, external_partition_set: ExternalPartitionSet, instance: DagsterInstance
    ) -> "ExternalPartitionNamesData":
        check.inst_param(external_partition_set, "external_partition_set", ExternalPartitionSet)

        # Prefer to return the names without calling out to user code if the
        # partition set allows it
        if external_partition_set.has_partition_name_data():
            return ExternalPartitionNamesData(
                partition_names=external_partition_set.get_partition_names(instance=instance)
            )

        return sync_get_external_partition_names_grpc(
            self.client, external_partition_set.repository_handle, external_partition_set.name
        )

    def get_external_schedule_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        schedule_name: str,
        scheduled_execution_time: Optional[datetime.datetime],
        log_key: Optional[Sequence[str]],
    ) -> "ScheduleExecutionData":
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(scheduled_execution_time, "scheduled_execution_time", PendulumDateTime)
        check.opt_list_param(log_key, "log_key", of_type=str)

        return sync_get_external_schedule_execution_data_grpc(
            self.client,
            instance,
            repository_handle,
            schedule_name,
            scheduled_execution_time,
            log_key,
        )

    def get_external_sensor_execution_data(
        self,
        instance: DagsterInstance,
        repository_handle: RepositoryHandle,
        name: str,
        last_tick_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
        log_key: Optional[Sequence[str]],
        last_sensor_start_time: Optional[float],
    ) -> "SensorExecutionData":
        from dagster._api.snapshot_sensor import sync_get_external_sensor_execution_data_grpc

        return sync_get_external_sensor_execution_data_grpc(
            self.client,
            instance,
            repository_handle,
            name,
            last_tick_completion_time,
            last_run_key,
            cursor,
            log_key,
            last_sensor_start_time,
        )

    def get_external_partition_set_execution_param_data(
        self,
        repository_handle: RepositoryHandle,
        partition_set_name: str,
        partition_names: Sequence[str],
        instance: DagsterInstance,
    ) -> "ExternalPartitionSetExecutionParamData":
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.sequence_param(partition_names, "partition_names", of_type=str)

        return sync_get_external_partition_set_execution_param_data_grpc(
            self.client, repository_handle, partition_set_name, partition_names, instance
        )

    def get_external_notebook_data(self, notebook_path: str) -> bytes:
        check.str_param(notebook_path, "notebook_path")
        return sync_get_streaming_external_notebook_data_grpc(self.client, notebook_path)

    def get_dagster_library_versions(self) -> Optional[Mapping[str, str]]:
        return self._dagster_library_versions
