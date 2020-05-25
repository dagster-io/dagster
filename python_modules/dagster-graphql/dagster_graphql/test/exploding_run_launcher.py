from dagster.core.launcher import RunLauncher
from dagster.serdes import ConfigurableClass


class ExplodingRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return ExplodingRunLauncher(inst_data=inst_data)

    def launch_run(self, instance, run, external_pipeline=None):
        raise NotImplementedError('The entire purpose of this is to throw on launch')

    def join(self):
        '''Nothing to join on since all executions are synchronous.'''
