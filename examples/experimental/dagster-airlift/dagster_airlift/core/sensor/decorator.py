from typing import Callable, Sequence

from dagster import AssetMaterialization, SensorDefinition

from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.airflow_instance import AirflowInstance, DagRun, TaskInstance

from .builder import build_airflow_polling_sensor

AirflowDagsterEventTranslationFn = Callable[
    [DagRun, Sequence[TaskInstance]], Sequence[AssetMaterialization]
]


def airflow_event_sensor(
    airflow_instance: AirflowInstance,
    airflow_data: AirflowDefinitionsData,
    minimum_interval_seconds,
) -> Callable[[AirflowDagsterEventTranslationFn], SensorDefinition]:
    def inner(fn: AirflowDagsterEventTranslationFn) -> SensorDefinition:
        return build_airflow_polling_sensor(
            airflow_instance=airflow_instance,
            airflow_data=airflow_data,
            event_translation_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
        )

    return inner
