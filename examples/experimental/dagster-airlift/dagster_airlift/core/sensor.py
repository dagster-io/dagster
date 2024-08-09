from collections import defaultdict
from datetime import timedelta
from typing import Dict, Sequence, Set

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

from .airflow_instance import AirflowInstance
from .utils import get_dag_id_from_asset


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
        toposorted_keys_per_dag = retrieve_toposorted_dag_keys(repository_def)

        last_effective_date = (
            datetime_from_timestamp(float(context.cursor))
            if context.cursor
            else get_current_datetime() - timedelta(days=1)
        )
        current_date = get_current_datetime()
        materializations_to_report = []
        for dag_id, topo_order_keys in toposorted_keys_per_dag.items():
            # For now, we materialize assets representing tasks only when the whole dag completes.
            # With a more robust cursor that can let us know when we've seen a particular task run already, then we can relax this constraint.
            for dag_run in airflow_instance.get_dag_runs(dag_id, last_effective_date, current_date):
                # If the dag run succeeded, add materializations for all assets referring to dags.
                if dag_run["state"] != "success":
                    raise Exception("Should only see successful dag runs at this point.")
                for asset_key in topo_order_keys:
                    asset_node = repository_def.asset_graph.get(asset_key)
                    spec = asset_node.to_asset_spec()
                    task_id = spec.tags.get("airlift/task_id")
                    details_link = (
                        airflow_instance.get_dag_run_url(dag_id, dag_run["dag_run_id"])
                        if task_id is None
                        else airflow_instance.get_task_instance_url(
                            dag_id, task_id, dag_run["dag_run_id"]
                        )
                    )
                    metadata = {
                        "Airflow Run ID": dag_run["dag_run_id"],
                        "Run Metadata (raw)": JsonMetadataValue(dag_run),
                        "Start Date": TimestampMetadataValue(
                            airflow_instance.timestamp_from_airflow_date(dag_run["start_date"])
                        ),
                        "End Date": TimestampMetadataValue(
                            airflow_instance.timestamp_from_airflow_date(dag_run["end_date"])
                        ),
                        "Run Type": dag_run["run_type"],
                        "Airflow Config": JsonMetadataValue(dag_run["conf"]),
                        "Run Details": MarkdownMetadataValue(f"[View]({details_link})"),
                        "Creation Timestamp": TimestampMetadataValue(get_current_timestamp()),
                    }
                    if task_id:
                        metadata["Task Logs"] = MarkdownMetadataValue(
                            f"[View Logs]({airflow_instance.get_task_instance_log_url(dag_id, task_id, dag_run['dag_run_id'])})"
                        )

                    materializations_to_report.append(
                        AssetMaterialization(
                            asset_key=asset_key,
                            description=dag_run["note"],
                            metadata=metadata,
                        )
                    )
        context.update_cursor(str(current_date.timestamp()))
        return SensorResult(
            asset_events=materializations_to_report,
        )

    return airflow_dag_sensor


def retrieve_toposorted_dag_keys(
    repository_def: RepositoryDefinition,
) -> Dict[str, Sequence[AssetKey]]:
    """For each dag, retrieve the topologically sorted list of asset keys."""
    # First, we need to retrieve the upstreams for each asset key
    upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    asset_keys_per_dag: Dict[str, Set[AssetKey]] = defaultdict(set)
    for assets_def in repository_def.assets_defs_by_key.values():
        # We could be more specific about the checks here to ensure that there's only one asset key
        # specifying the dag, and that all others have a task id.
        dag_id = get_dag_id_from_asset(assets_def)
        if dag_id is None:
            continue
        for spec in assets_def.specs:
            for dep in spec.deps:
                upstreams_asset_dependency_graph[spec.key].add(dep.asset_key)
            asset_keys_per_dag[dag_id].add(spec.key)

    # Now, we can retrieve the topologically sorted list of asset keys for each dag
    dag_keys_to_toposorted_asset_keys: Dict[str, Sequence[AssetKey]] = {}
    for dag_id, asset_keys in asset_keys_per_dag.items():
        dag_keys_to_toposorted_asset_keys[dag_id] = toposort_keys(
            asset_keys, upstreams_asset_dependency_graph
        )

    return dag_keys_to_toposorted_asset_keys


def toposort_keys(
    keys_in_subgraph: Set[AssetKey], upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]]
) -> Sequence[AssetKey]:
    narrowed_asset_dependency_graph = {
        key: {dep for dep in upstreams_asset_dependency_graph[key] if dep in keys_in_subgraph}
        for key in keys_in_subgraph
    }
    return toposort_flatten(narrowed_asset_dependency_graph)
