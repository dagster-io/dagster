from collections.abc import Iterable, Sequence

from dagster import (
    AssetMaterialization,
    AssetObservation,
    AssetSpec,
    Definitions,
    SensorEvaluationContext,
)
from dagster_airlift.core import (
    AirflowDefinitionsData,
    AssetEvent,
    build_defs_from_airflow_instance,
)
from dagster_airlift.core.top_level_dag_def_api import assets_with_task_mappings

from kitchen_sink.airflow_instance import local_airflow_instance


def observations_from_materializations(
    context: SensorEvaluationContext,
    airflow_data: AirflowDefinitionsData,
    materializations: Sequence[AssetMaterialization],
) -> Iterable[AssetEvent]:
    """Construct AssetObservations from AssetMaterializations."""
    for materialization in materializations:
        yield AssetObservation(
            asset_key=materialization.asset_key,
            description=materialization.description,
            metadata=materialization.metadata,
            tags=materialization.tags,
        )


def build_mapped_defs() -> Definitions:
    return build_defs_from_airflow_instance(
        airflow_instance=local_airflow_instance(),
        defs=Definitions(
            assets=assets_with_task_mappings(
                dag_id="simple_unproxied_dag",
                task_mappings={
                    "print_task": [AssetSpec("my_asset")],
                    "downstream_print_task": [AssetSpec("my_downstream_asset", deps=["my_asset"])],
                },
            ),
        ),
        event_transformer_fn=observations_from_materializations,
        sensor_minimum_interval_seconds=1,
    )


defs = build_mapped_defs()
