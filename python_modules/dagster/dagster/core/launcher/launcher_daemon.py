import os
import subprocess

from dagster import EventMetadataEntry, check, seven
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from .launcher_base import RunLauncher


class DaemonRunLauncher(RunLauncher, ConfigurableClass):
    '''RunLauncher that starts daemon process for each pipeline run

    Encapsulates each pipeline run in a separate, isolated invocation of ``dagster-graphql``.

    You may configure a Dagster instance to use this RunLauncher by adding a section to your
    ``dagster.yaml`` like the following:

    .. code-block:: yaml

        run_launcher:
            module: dagster.core.launcher
            class: DaemonRunLauncher
            config: {}
    '''
    def __init__(self, inst_data=None):
        print('FOOOOOOO INIT')
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def launch_run(self, instance, run):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(run, 'run', PipelineRun)

        job_name = 'dagster-run-%s' % run.run_id

        print('HIHIHIHIHIHIHIHI')

        subprocess.Popen([
            'dagster-graphql',
            '-p', 'startPipelineExecutionForCreatedRun',
            '-v', seven.json.dumps({'runId': run.run_id}),
        ], env=os.environ)

        instance.report_engine_event(
            'Daemon job launched',
            run,
            EngineEventData(
                [
                    EventMetadataEntry.text(job_name, 'Daemon Job name'),
                    EventMetadataEntry.text(run.run_id, 'Run ID'),
                ]
            ),
            cls=DaemonRunLauncher,
        )
        return run
