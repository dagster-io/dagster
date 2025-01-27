from collections.abc import Mapping
from typing import Any, Optional

from dagster._core.events import EngineEventData
from dagster._core.storage.dagster_run import DagsterRun
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self

from dagster_aws.ecs.container_context import EcsContainerContext
from dagster_aws.ecs.launcher import EcsRunLauncher


class CustomECSRunLauncher(EcsRunLauncher):
    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
        task_definition=None,
        container_name="run",
        secrets=None,
        secrets_tag="dagster",
        env_vars=None,
        include_sidecars=False,
    ):
        super().__init__(
            inst_data=inst_data,
            task_definition=task_definition,
            container_name=container_name,
            secrets=secrets,
            secrets_tag=secrets_tag,
            env_vars=env_vars,
            include_sidecars=include_sidecars,
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    def get_cpu_and_memory_overrides(
        self, container_context: EcsContainerContext, run: DagsterRun
    ) -> Mapping[str, str]:
        return {"cpu": "4096", "memory": "16384"}

    def _get_task_overrides(
        self, container_context: EcsContainerContext, run: DagsterRun
    ) -> Mapping[str, Any]:
        return {"ephemeralStorage": {"sizeInGiB": 128}}

    def report_launch_events(
        self, run: DagsterRun, arn: Optional[str] = None, cluster: Optional[str] = None
    ):
        self._instance.report_engine_event(
            message="Launching run in custom ECS task",
            dagster_run=run,
            engine_event_data=EngineEventData({"Run ID": run.run_id}),
        )
