from dagster import Field, Selector
from dagster.core.launcher import RunLauncher
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from dagster.utils.backcompat import experimental


@experimental
class RenderRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None, service=None):
        self._inst_data = inst_data
        self._service = service

    @property
    def inst_data(self):
        return self._inst_data

    @staticmethod
    def from_config_value(inst_data, config_value):
        return RenderRunLauncher(inst_data=inst_data, **config_value)

    @classmethod
    def config_type(cls):
        return {
            "service": Field(
                Selector(
                    {
                        "id": Field(
                            str,
                            description=(
                                "Set this value if you know the serviceId of the Render service "
                                "to launch when creating jobs to execute runs."
                            ),
                        ),
                        "name": Field(
                            str,
                            description=(
                                "Set this value if you know the name of the Render service to "
                                "launch when creating jobs to execute runs. This service must be "
                                "unique in your Render account. By default, the run launcher will "
                                "look for a service called 'dagster'."
                            ),
                        ),
                    }
                ),
                default_value={"name": "dagster"},
            )
        }

    def launch_run(self, context):
        """Launch a run in a Render job."""

        run = context.pipeline_run
        pipeline_origin = context.pipeline_code_origin

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=pipeline_origin,
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )
        command = ["dagster", "api", "execute_run", input_json]

        self._instance.report_engine_event(
            message=f"Launching run in Render job with plan_id: ",
            pipeline_run=run,
            cls=self.__class__,
        )

    def can_terminate(self, run_id):
        return False

    def terminate(self, run_id):
        raise NotImplementedError(
            "Shouldn't be here: Render jobs can't be terminated programmatically."
        )
