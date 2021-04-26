import datetime
import sys
import threading
from abc import abstractmethod, abstractproperty
from contextlib import AbstractContextManager

from dagster import check
from dagster.api.get_server_id import sync_get_server_id
from dagster.api.list_repositories import sync_list_repositories_grpc
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
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation.external import (
    ExternalExecutionPlan,
    ExternalPipeline,
    ExternalRepository,
)
from dagster.core.host_representation.grpc_server_state_subscriber import (
    LocationStateChangeEvent,
    LocationStateChangeEventType,
)
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
    get_partition_config,
    get_partition_names,
    get_partition_set_execution_param_data,
    get_partition_tags,
)
from dagster.seven import PendulumDateTime
from dagster.utils import merge_dicts
from dagster.utils.hosted_user_process import external_repo_from_def

from .selector import PipelineSelector


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
    def get_repository(self, name):
        pass

    @abstractmethod
    def has_repository(self, name):
        pass

    @abstractmethod
    def get_repositories(self):
        pass

    def get_repository_names(self):
        return list(self.get_repositories().keys())

    @property
    def name(self):
        return self.origin.location_name

    @abstractmethod
    def get_external_execution_plan(
        self, external_pipeline, run_config, mode, step_keys_to_execute, known_state
    ):
        pass

    @abstractmethod
    def get_subset_external_pipeline_result(self, selector):
        pass

    @abstractmethod
    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        pass

    @abstractmethod
    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        pass

    @abstractmethod
    def get_external_partition_names(self, repository_handle, partition_set_name):
        pass

    @abstractmethod
    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        pass

    @abstractmethod
    def get_external_schedule_execution_data(
        self,
        instance,
        repository_handle,
        schedule_name,
        scheduled_execution_time,
    ):
        pass

    @abstractmethod
    def get_external_sensor_execution_data(
        self, instance, repository_handle, name, last_completion_time, last_run_key
    ):
        pass

    @abstractproperty
    def is_reload_supported(self):
        pass

    def __del__(self):
        self.cleanup()

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.cleanup()

    def cleanup(self):
        pass

    def add_state_subscriber(self, subscriber):
        pass

    @abstractproperty
    def origin(self):
        pass

    def get_display_metadata(self):
        return merge_dicts(
            self.origin.get_display_metadata(),
            ({"image": self.container_image} if self.container_image else {}),
        )

    @abstractproperty
    def executable_path(self):
        pass

    @abstractproperty
    def container_image(self):
        pass

    @abstractproperty
    def repository_code_pointer_dict(self):
        pass

    def get_repository_python_origin(self, repository_name):
        if repository_name not in self.repository_code_pointer_dict:
            raise DagsterInvariantViolationError(
                "Unable to find repository name {} on GRPC server.".format(repository_name)
            )

        code_pointer = self.repository_code_pointer_dict[repository_name]
        return RepositoryPythonOrigin(
            executable_path=self.executable_path,
            code_pointer=code_pointer,
            container_image=self.container_image,
        )


class InProcessRepositoryLocation(RepositoryLocation):
    def __init__(self, origin):
        self._origin = check.inst_param(origin, "origin", InProcessRepositoryLocationOrigin)

        self._recon_repo = self._origin.recon_repo

        repo_def = self._recon_repo.get_definition()
        pointer = self._recon_repo.pointer

        self._repository_code_pointer_dict = {repo_def.name: pointer}

        def_name = repo_def.name

        self._external_repo = external_repo_from_def(
            repo_def,
            RepositoryHandle(repository_name=def_name, repository_location=self),
        )
        self._repositories = {self._external_repo.name: self._external_repo}

    @property
    def is_reload_supported(self):
        return False

    @property
    def origin(self):
        return self._origin

    @property
    def executable_path(self):
        return sys.executable

    @property
    def container_image(self):
        return self._recon_repo.container_image

    @property
    def repository_code_pointer_dict(self):
        return self._repository_code_pointer_dict

    def get_reconstructable_pipeline(self, name):
        return self.get_reconstructable_repository().get_reconstructable_pipeline(name)

    def get_reconstructable_repository(self):
        return self.origin.recon_repo

    def get_repository(self, name):
        return self._repositories[name]

    def has_repository(self, name):
        return name in self._repositories

    def get_repositories(self):
        return self._repositories

    def get_subset_external_pipeline_result(self, selector):
        check.inst_param(selector, "selector", PipelineSelector)
        check.invariant(
            selector.location_name == self.name,
            "PipelineSelector location_name mismatch, got {selector.location_name} expected {self.name}".format(
                self=self, selector=selector
            ),
        )

        from dagster.grpc.impl import get_external_pipeline_subset_result

        return get_external_pipeline_subset_result(
            self.get_reconstructable_pipeline(selector.pipeline_name), selector.solid_selection
        )

    def get_external_execution_plan(
        self,
        external_pipeline,
        run_config,
        mode,
        step_keys_to_execute,
        known_state,
    ):
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.dict_param(run_config, "run_config")
        check.str_param(mode, "mode")
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)

        return ExternalExecutionPlan(
            execution_plan_snapshot=snapshot_from_execution_plan(
                create_execution_plan(
                    pipeline=self.get_reconstructable_pipeline(
                        external_pipeline.name
                    ).subset_for_execution_from_existing_pipeline(
                        external_pipeline.solids_to_execute
                    ),
                    run_config=run_config,
                    mode=mode,
                    step_keys_to_execute=step_keys_to_execute,
                    known_state=known_state,
                ),
                external_pipeline.identifying_pipeline_snapshot_id,
            ),
            represented_pipeline=external_pipeline,
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_config(
            recon_repo=self._recon_repo,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return get_partition_tags(
            recon_repo=self._recon_repo,
            partition_set_name=partition_set_name,
            partition_name=partition_name,
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")

        return get_partition_names(
            recon_repo=self._recon_repo,
            partition_set_name=partition_set_name,
        )

    def get_external_schedule_execution_data(
        self,
        instance,
        repository_handle,
        schedule_name,
        scheduled_execution_time,
    ):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(scheduled_execution_time, "scheduled_execution_time", PendulumDateTime)

        return get_external_schedule_execution(
            self._recon_repo,
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
        self, instance, repository_handle, name, last_completion_time, last_run_key
    ):
        return get_external_sensor_execution(
            self._recon_repo, instance.get_ref(), name, last_completion_time, last_run_key
        )

    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.list_param(partition_names, "partition_names", of_type=str)

        return get_partition_set_execution_param_data(
            self._recon_repo,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )


class GrpcServerRepositoryLocation(RepositoryLocation):
    def __init__(
        self,
        origin,
        host=None,
        port=None,
        socket=None,
        server_id=None,
        heartbeat=False,
        watch_server=True,
        grpc_server_registry=None,
    ):
        from dagster.grpc.client import DagsterGrpcClient, client_heartbeat_thread
        from dagster.grpc.server_watcher import create_grpc_watch_thread
        from .grpc_server_registry import GrpcServerRegistry

        self._origin = check.inst_param(origin, "origin", RepositoryLocationOrigin)

        self.grpc_server_registry = check.opt_inst_param(
            grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
        )

        if isinstance(self._origin, GrpcServerRepositoryLocationOrigin):
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
        self._repository_code_pointer_dict = None

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

            if self._watch_server:
                self._state_subscribers = []
                self._watch_thread_shutdown_event, self._watch_thread = create_grpc_watch_thread(
                    self.client,
                    on_updated=lambda new_server_id: self._send_state_event_to_subscribers(
                        LocationStateChangeEvent(
                            LocationStateChangeEventType.LOCATION_UPDATED,
                            location_name=self.name,
                            message="Server has been updated.",
                            server_id=new_server_id,
                        )
                    ),
                    on_error=lambda: self._send_state_event_to_subscribers(
                        LocationStateChangeEvent(
                            LocationStateChangeEventType.LOCATION_ERROR,
                            location_name=self.name,
                            message="Unable to reconnect to server. You can reload the server once it is "
                            "reachable again",
                        )
                    ),
                )

                self._watch_thread.start()

            self._executable_path = list_repositories_response.executable_path
            self._repository_code_pointer_dict = (
                list_repositories_response.repository_code_pointer_dict
            )

            self._container_image = self._reload_current_image()

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

    def add_state_subscriber(self, subscriber):
        if self._watch_server:
            self._state_subscribers.append(subscriber)

    def _send_state_event_to_subscribers(self, event):
        check.inst_param(event, "event", LocationStateChangeEvent)
        for subscriber in self._state_subscribers:
            subscriber.handle_event(event)

    @property
    def origin(self):
        return self._origin

    @property
    def container_image(self):
        return self._container_image

    @property
    def repository_code_pointer_dict(self):
        return self._repository_code_pointer_dict

    @property
    def executable_path(self):
        return self._executable_path

    @property
    def port(self):
        return self._port

    @property
    def socket(self):
        return self._socket

    @property
    def host(self):
        return self._host

    @property
    def use_ssl(self):
        return self._use_ssl

    def _reload_current_image(self):
        return self.client.get_current_image().current_image

    def cleanup(self):
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
    def is_reload_supported(self):
        return True

    def get_repository(self, name):
        check.str_param(name, "name")
        return self.get_repositories()[name]

    def has_repository(self, name):
        return name in self.get_repositories()

    def get_repositories(self):
        return self.external_repositories

    def get_external_execution_plan(
        self,
        external_pipeline,
        run_config,
        mode,
        step_keys_to_execute,
        known_state,
    ):
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.dict_param(run_config, "run_config")
        check.str_param(mode, "mode")
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
        check.opt_inst_param(known_state, "known_state", KnownExecutionState)

        execution_plan_snapshot_or_error = sync_get_external_execution_plan_grpc(
            api_client=self.client,
            pipeline_origin=external_pipeline.get_external_origin(),
            run_config=run_config,
            mode=mode,
            pipeline_snapshot_id=external_pipeline.identifying_pipeline_snapshot_id,
            solid_selection=external_pipeline.solid_selection,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
        )

        return ExternalExecutionPlan(
            execution_plan_snapshot=execution_plan_snapshot_or_error,
            represented_pipeline=external_pipeline,
        )

    def get_subset_external_pipeline_result(self, selector):
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
            self.client, pipeline_handle.get_external_origin(), selector.solid_selection
        )

    def get_external_partition_config(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_config_grpc(
            self.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_tags(self, repository_handle, partition_set_name, partition_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.str_param(partition_name, "partition_name")

        return sync_get_external_partition_tags_grpc(
            self.client, repository_handle, partition_set_name, partition_name
        )

    def get_external_partition_names(self, repository_handle, partition_set_name):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")

        return sync_get_external_partition_names_grpc(
            self.client, repository_handle, partition_set_name
        )

    def get_external_schedule_execution_data(
        self,
        instance,
        repository_handle,
        schedule_name,
        scheduled_execution_time,
    ):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(schedule_name, "schedule_name")
        check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", datetime.datetime
        )

        return sync_get_external_schedule_execution_data_grpc(
            self.client,
            instance,
            repository_handle,
            schedule_name,
            scheduled_execution_time,
        )

    def get_external_sensor_execution_data(
        self, instance, repository_handle, name, last_completion_time, last_run_key
    ):
        return sync_get_external_sensor_execution_data_grpc(
            self.client,
            instance,
            repository_handle,
            name,
            last_completion_time,
            last_run_key,
        )

    def get_external_partition_set_execution_param_data(
        self, repository_handle, partition_set_name, partition_names
    ):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.str_param(partition_set_name, "partition_set_name")
        check.list_param(partition_names, "partition_names", of_type=str)

        return sync_get_external_partition_set_execution_param_data_grpc(
            self.client, repository_handle, partition_set_name, partition_names
        )
