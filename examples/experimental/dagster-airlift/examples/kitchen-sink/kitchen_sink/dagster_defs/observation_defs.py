from typing import Iterable, Sequence

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
    dag_defs,
    task_defs,
)

from .airflow_instance import local_airflow_instance


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
        defs=Definitions.merge(
            dag_defs(
                "simple_unproxied_dag",
                task_defs("print_task", Definitions(assets=[AssetSpec("my_asset")])),
                task_defs(
                    "downstream_print_task",
                    Definitions(assets=[AssetSpec("my_downstream_asset", deps=["my_asset"])]),
                ),
            ),
        ),
        event_transformer_fn=observations_from_materializations,
    )


defs = build_mapped_defs()
