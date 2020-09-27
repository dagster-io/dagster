from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.serdes import ConfigurableClass

from .base import RunLauncher
from .cli_api_run_launcher import CliApiRunLauncher
from .grpc_run_launcher import GRPC_REPOSITORY_LOCATION_HANDLE_TYPES, GrpcRunLauncher


class DefaultRunLauncher(RunLauncher, ConfigurableClass):
    """Default run launcher.

    This run launcher is aware of instance- and repository-level settings governing whether
    repositories should be loaded and runs launched over the legacy CLI API or over GRPC.
    """

    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self._cli_api_run_launcher = CliApiRunLauncher()
        self._grpc_run_launcher = GrpcRunLauncher()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, _config_value):
        return DefaultRunLauncher(inst_data=inst_data,)

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)

        self._cli_api_run_launcher.initialize(instance)
        self._grpc_run_launcher.initialize(instance)

    def launch_run(self, instance, run, external_pipeline):
        repository_location_handle = external_pipeline.repository_handle.repository_location_handle
        if isinstance(repository_location_handle, GRPC_REPOSITORY_LOCATION_HANDLE_TYPES,):
            return self._grpc_run_launcher.launch_run(instance, run, external_pipeline)
        else:
            return self._cli_api_run_launcher.launch_run(instance, run, external_pipeline)

    def can_terminate(self, run_id):
        return self._cli_api_run_launcher.can_terminate(
            run_id
        ) or self._grpc_run_launcher.can_terminate(run_id)

    def terminate(self, run_id):
        if self._cli_api_run_launcher.can_terminate(run_id):
            return self._cli_api_run_launcher.terminate(run_id)
        elif self._grpc_run_launcher.can_terminate(run_id):
            return self._grpc_run_launcher.terminate(run_id)
        else:
            instance = self._cli_api_run_launcher._instance  # pylint: disable=protected-access
            if not instance:
                return False

            run = instance.get_run_by_id(run_id)
            if not run:
                return False

            instance.report_engine_event(
                message="Pipeline was not terminated since {} and {} could not find in-progress run.".format(
                    self._cli_api_run_launcher.__class__.__name__,
                    self._grpc_run_launcher.__class__.__name__,
                ),
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

    def dispose(self):
        self._cli_api_run_launcher.dispose()
        self._grpc_run_launcher.dispose()

    def join(self, timeout=30):
        self._cli_api_run_launcher.join(timeout=timeout)
        self._grpc_run_launcher.join(timeout=timeout)

    def cleanup_managed_grpc_servers(self):
        self._grpc_run_launcher.cleanup_managed_grpc_servers()
