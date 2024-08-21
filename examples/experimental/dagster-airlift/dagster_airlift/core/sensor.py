from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Sequence, Set, Tuple

from dagster import (
    AssetKey,
    AssetMaterialization,
    DefaultSensorStatus,
    JsonMetadataValue,
    MarkdownMetadataValue,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    TimestampMetadataValue,
    _check as check,
    sensor,
)
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.utils import toposort_flatten
from dagster._time import datetime_from_timestamp, get_current_datetime, get_current_timestamp

from .airflow_instance import AirflowInstance, TaskInstance
from .utils import MIGRATED_TAG, get_dag_id_from_asset, get_task_id_from_asset


def build_airflow_polling_sensor(
    airflow_instance: AirflowInstance,
) -> SensorDefinition:
    @sensor(
        name="airflow_dag_status_sensor",
        minimum_interval_seconds=1,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def airflow_dag_sensor(context: SensorEvaluationContext) -> SensorResult:
        """Sensor to report materialization events for each asset as new runs come in."""
        repository_def = check.not_none(context.repository_def)
        last_effective_date = (
            datetime_from_timestamp(float(context.cursor))
            if context.cursor
            else get_current_datetime() - timedelta(days=1)
        )
        current_date = get_current_datetime()
        materializations_to_report: List[Tuple[float, AssetMaterialization]] = []
        toposorted_keys = toposorted_asset_keys(repository_def)
        for dag_id, (dag_key, task_keys) in retrieve_unmigrated_dag_keys(repository_def).items():
            # For now, we materialize assets representing tasks only when the whole dag completes.
            # With a more robust cursor that can let us know when we've seen a particular task run already, then we can relax this constraint.
            for dag_run in airflow_instance.get_dag_runs(dag_id, last_effective_date, current_date):
                if not dag_run.success:
                    raise Exception("Should only see successful dag runs at this point.")

                metadata = {
                    "Airflow Run ID": dag_run.run_id,
                    "Run Metadata (raw)": JsonMetadataValue(dag_run.metadata),
                    "Run Type": dag_run.run_type,
                    "Airflow Config": JsonMetadataValue(dag_run.config),
                    "Creation Timestamp": TimestampMetadataValue(get_current_timestamp()),
                }
                # Add dag materialization
                dag_metadata = {
                    **metadata,
                    "Run Details": MarkdownMetadataValue(f"[View Run]({dag_run.url})"),
                    "Start Date": TimestampMetadataValue(dag_run.start_date),
                    "End Date": TimestampMetadataValue(dag_run.end_date),
                }
                materializations_to_report.append(
                    (
                        dag_run.end_date,
                        AssetMaterialization(
                            asset_key=dag_key,
                            description=dag_run.note,
                            metadata=dag_metadata,
                        ),
                    )
                )
                task_runs = {}
                for task_id, asset_key in task_keys:
                    task_run: TaskInstance = task_runs.get(
                        task_id, airflow_instance.get_task_instance(dag_id, task_id, dag_run.run_id)
                    )
                    task_runs[task_id] = task_run
                    task_metadata = {
                        **metadata,
                        "Run Details": MarkdownMetadataValue(f"[View Run]({task_run.details_url})"),
                        "Task Logs": MarkdownMetadataValue(f"[View Logs]({task_run.log_url})"),
                        "Start Date": TimestampMetadataValue(dag_run.start_date),
                        "End Date": TimestampMetadataValue(dag_run.end_date),
                    }
                    materializations_to_report.append(
                        (
                            task_run.end_date,
                            AssetMaterialization(
                                asset_key=asset_key,
                                description=task_run.note,
                                metadata=task_metadata,
                            ),
                        )
                    )
        # Sort materializations by end date and toposort order
        sorted_mats = sorted(
            materializations_to_report, key=lambda x: (x[0], toposorted_keys.index(x[1].asset_key))
        )
        context.update_cursor(str(current_date.timestamp()))
        return SensorResult(
            asset_events=[sorted_mat[1] for sorted_mat in sorted_mats],
        )

    return airflow_dag_sensor


def retrieve_unmigrated_dag_keys(
    repository_def: RepositoryDefinition,
) -> Dict[str, Tuple[AssetKey, Set[Tuple[str, AssetKey]]]]:
    """For each dag, retrieve the list of asset keys which correspond, and are unmigrated.
    The key representing the "peered" dag will always be retrieved, but assets whose tasks are marked as "migrated" will not.
    """
    # First, we need to retrieve the upstreams for each asset key
    key_per_dag = {}
    task_keys_per_dag = defaultdict(set)
    for assets_def in repository_def.assets_defs_by_key.values():
        # We could be more specific about the checks here to ensure that there's only one asset key
        # specifying the dag, and that all others have a task id.
        dag_id = get_dag_id_from_asset(assets_def)
        task_id = get_task_id_from_asset(assets_def)
        if dag_id is None:
            continue
        if task_id is None:
            key_per_dag[dag_id] = (
                assets_def.key
            )  # There should only be one key in the case of a "dag" asset
        else:
            migrated = (
                MIGRATED_TAG in assets_def.node_def.tags
                and assets_def.node_def.tags[MIGRATED_TAG] == "True"
            )
            if migrated:
                continue
            else:
                task_keys_per_dag[dag_id].update((task_id, spec.key) for spec in assets_def.specs)
    return {dag_id: (key, task_keys_per_dag[dag_id]) for dag_id, key in key_per_dag.items()}


def toposorted_asset_keys(
    repository_def: RepositoryDefinition,
) -> Sequence[AssetKey]:
    asset_dep_graph = defaultdict(set)  # upstreams
    for assets_def in repository_def.assets_defs_by_key.values():
        for spec in assets_def.specs:
            asset_dep_graph[spec.key].update(dep.asset_key for dep in spec.deps)

    return toposort_flatten(asset_dep_graph)
