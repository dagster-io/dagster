from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.serdes import ConfigurableClass

from .base import RunLauncher
from .grpc_run_launcher import GrpcRunLauncher


class DefaultRunLauncher(RunLauncher, ConfigurableClass):
    """Default run launcher. Delegates all operations to a GrpcRunLauncher.
    """

    def __init__(self, inst_data=None):
        self._inst_data = inst_data
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
        self._grpc_run_launcher.initialize(instance)

    def launch_run(self, instance, run, external_pipeline):
        return self._grpc_run_launcher.launch_run(instance, run, external_pipeline)

    def can_terminate(self, run_id):
        return self._grpc_run_launcher.can_terminate(run_id)

    def terminate(self, run_id):
        return self._grpc_run_launcher.terminate(run_id)

    def dispose(self):
        self._grpc_run_launcher.dispose()

    def join(self, timeout=30):
        self._grpc_run_launcher.join(timeout=timeout)

    def cleanup_managed_grpc_servers(self):
        self._grpc_run_launcher.cleanup_managed_grpc_servers()
