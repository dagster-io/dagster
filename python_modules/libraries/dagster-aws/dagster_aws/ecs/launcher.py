from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass

from .client import ECSClient


class ECSRunLauncher(RunLauncher, ConfigurableClass):

    # TODO: Handle multiple runs per RunLauncher
    def __init__(
        self,
        key_id,
        access_key,
        command,
        entrypoint,
        family='echostart',
        containername='basictest',
        imagename="httpd:2.4",
        memory='512',
        cpu='256',
        inst_data=None,
        region_name='us-east-2',
        launch_type='FARGATE',
    ):
        self._inst_data = inst_data
        self.client = ECSClient(
            region_name=region_name, key_id=key_id, access_key=access_key, launch_type=launch_type
        )
        self.client.set_and_register_task(
            command,
            entrypoint,
            family=family,
            containername=containername,
            imagename=imagename,
            memory=memory,
            cpu=cpu,
        )

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def launch_run(self, instance, run, external_pipeline=None):
        # currently ignoring external pipeline
        if external_pipeline is None:
            pass
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(run, 'run', PipelineRun)

        instance.create_run(run)
        # this maps run configuration to task overrides
        # this way we can pass in parameters from the dagit configuration that user has entered in the UI
        overrides = self.generate_task_overrides(run)
        self.client.run_task(overrides=overrides)

    def generate_task_overrides(self, run):
        return {
            "containerOverrides": [
                {
                    "name": self.client.container_name,
                    "environment": [
                        {"name": "PIPELINE", "value": run.pipeline_name},
                        # possibly pull from run.environment_dict['solids'] other data that user might entered in the UI
                    ],
                },
            ],
        }

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')
        return self.client.check_if_done

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')
        check.not_implemented('Termination not yet implemented')
