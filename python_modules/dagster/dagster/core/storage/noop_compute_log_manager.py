import dagster._check as check
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from .compute_log_manager import MAX_BYTES_FILE_READ, ComputeLogFileData, ComputeLogManager


class NoOpComputeLogManager(ComputeLogManager, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return NoOpComputeLogManager(inst_data=inst_data, **config_value)

    def enabled(self, _pipeline_run, _step_key):
        return False

    def _watch_logs(self, pipeline_run, step_key=None):
        pass

    def is_watch_completed(self, run_id, key):
        return True

    def on_watch_start(self, pipeline_run, step_key):
        pass

    def on_watch_finish(self, pipeline_run, step_key):
        pass

    def download_url(self, run_id, key, io_type):
        return None

    def read_logs_file(self, run_id, key, io_type, cursor=0, max_bytes=MAX_BYTES_FILE_READ):
        return ComputeLogFileData(
            path="{}.{}".format(key, io_type), data=None, cursor=0, size=0, download_url=None
        )

    def on_subscribe(self, subscription):
        pass

    def on_unsubscribe(self, subscription):
        pass
