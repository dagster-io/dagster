import datetime
import json
from datetime import timedelta
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import requests
from dagster import (
    AssetDep,
    AssetKey,
    AssetMaterialization,
    AssetsDefinition,
    AssetSpec,
    JsonMetadataValue,
    MarkdownMetadataValue,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    TimestampMetadataValue,
    multi_asset,
    sensor,
)
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster_dbt import build_dbt_asset_specs
from pydantic import BaseModel


class DagInfo(BaseModel):
    dag_id: str
    metadata: Dict[str, Any]


class TaskMapping(NamedTuple):
    """Maps a task in an Airflow DAG to an asset spec in Dagster."""

    dag_id: str
    task_id: str
    # A constrained version of AssetSpec that only includes the fields we can easily concatenate.
    key: AssetKey
    deps: List[AssetDep] = []
    tags: Mapping[str, str] = {}
    metadata: Mapping[str, Any] = {}
    group: Optional[str] = None


def assets_defs_from_airflow_instance(
    airflow_webserver_url: str,
    auth: Tuple[str, str],
    instance_name: str,
    task_maps: Sequence[TaskMapping] = [],
) -> List[AssetsDefinition]:
    api_url = f"{airflow_webserver_url}/api/v1"
    dag_infos: List[DagInfo] = []

    # First, we attempt to fetch all the DAGs present in the Airflow instance.
    response = requests.get(f"{api_url}/dags", auth=auth)
    if response.status_code == 200:
        dags = response.json()
        for dag in dags["dags"]:
            dag_infos.append(
                DagInfo(
                    dag_id=dag["dag_id"],
                    metadata=dag,
                )
            )

    else:
        raise Exception(
            f"Failed to fetch DAGs. Status code: {response.status_code}, Message: {response.text}"
        )

    asset_specs = []

    # All the assets which map to tasks within a given dag should be considered "upstream" of the dag.
    dag_id_to_upstream_specs: Dict[str, List[AssetSpec]] = {}

    for task in task_maps:
        response = requests.get(f"{api_url}/dags/{task.dag_id}/tasks/{task.task_id}", auth=auth)
        if response.status_code == 200:
            task_info = response.json()
            joined_metadata = {
                **task.metadata,
                **{
                    "Task Info (raw)": JsonMetadataValue(task_info),
                    "Task ID": task.task_id,
                    "Dag ID": task.dag_id,
                    "Link to Task": MarkdownMetadataValue(
                        f"[View Task]({airflow_webserver_url}/dags/{task.dag_id}/{task.task_id})"
                    ),
                },
            }
            joined_tags = {
                **task.tags,
                **{"dagster/compute_kind": "airflow"},
            }
            asset_spec = AssetSpec(
                deps=task.deps,
                key=task.key,
                description=f"A data asset materialized by task {task.task_id} within airflow dag {task.dag_id}.",
                metadata=joined_metadata,
                tags=joined_tags,
                group_name=task.group,
            )
            asset_specs.append(asset_spec)
            dag_id_to_upstream_specs[task.dag_id] = dag_id_to_upstream_specs.get(
                task.dag_id, []
            ) + [asset_spec]
        else:
            raise Exception(
                f"Failed to fetch task info for {task.dag_id}/{task.task_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    dag_id_to_asset_key: Dict[str, AssetKey] = {}

    for dag_info in dag_infos:
        dag_id_to_asset_key[dag_info.dag_id] = AssetKey(
            [instance_name, "dag", f"{dag_info.dag_id}__successful_run"]
        )
        metadata = {
            "Dag Info (raw)": JsonMetadataValue(dag_info.metadata),
            "Dag ID": dag_info.dag_id,
            "Link to DAG": MarkdownMetadataValue(
                f"[View DAG]({airflow_webserver_url}/dags/{dag_info.dag_id})"
            ),
        }
        # Attempt to retrieve source code from the DAG.
        file_token = dag_info.metadata["file_token"]
        url = f"{api_url}/dagSources/{file_token}"
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            metadata["Source Code"] = MarkdownMetadataValue(
                f"""
```python
{response.text}
```
                """
            )
        upstream_specs = dag_id_to_upstream_specs.get(dag_info.dag_id, [])
        leaf_upstreams = get_leaf_specs(upstream_specs)
        asset_specs.append(
            AssetSpec(
                key=dag_id_to_asset_key[dag_info.dag_id],
                description=f"A materialization corresponds to a successful run of airflow DAG {dag_info.dag_id}.",
                metadata=metadata,
                tags={"dagster/compute_kind": "airflow"},
                group_name=f"{instance_name}__dags",
                deps=[AssetDep(asset=spec.key) for spec in leaf_upstreams],
            )
        )

    assets_defs = []
    for i, spec in enumerate(asset_specs):

        @multi_asset(specs=[spec], name=f"asset_{i}", compute_kind="airflow")
        def _the_asset():
            raise NotImplementedError("This is a placeholder function that should never be called.")

        assets_defs.append(_the_asset)
    return assets_defs


def build_airflow_polling_sensor(
    airflow_webserver_url: str,
    auth: Tuple[str, str],
    airflow_asset_specs: List[AssetSpec],
) -> SensorDefinition:
    api_url = f"{airflow_webserver_url}/api/v1"

    @sensor(name="airflow_dag_status_sensor")
    def airflow_dag_sensor(context: SensorEvaluationContext) -> SensorResult:
        """Sensor to report materialization events for each asset as new runs come in."""
        last_effective_date = (
            datetime_from_timestamp(float(context.cursor))
            if context.cursor
            else get_current_datetime() - timedelta(days=1)
        )
        current_date = get_current_datetime()
        materializations_to_report = []
        specs_by_dag_id: Dict[str, List[AssetSpec]] = {}
        for spec in airflow_asset_specs:
            dag_id = spec.metadata["Dag ID"]
            if dag_id not in specs_by_dag_id:
                specs_by_dag_id[dag_id] = []
            specs_by_dag_id[dag_id].append(spec)
        for dag, specs in specs_by_dag_id.items():
            response = requests.get(
                f"{api_url}/dags/{dag}/dagRuns",
                auth=auth,
                params={
                    "updated_at_gte": last_effective_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "updated_at_lte": current_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                },
            )
            # For now, we materialize assets representing tasks only when the whole dag completes.
            # With a more robust cursor that can let us know when we've seen a particular task run already, then we can relax this constraint.
            for dag_run in response.json()["dag_runs"]:
                # If the dag run succeeded, add materializations for all assets referring to dags.
                if dag_run["state"] != "success":
                    raise Exception("Should not have seen a non-successful dag run.")
                    continue

                materializations_to_report.extend(
                    [
                        AssetMaterialization(
                            asset_key=spec.key,
                            description=dag_run["note"],
                            metadata={
                                "Airflow Run ID": dag_run["dag_run_id"],
                                "Run Metadata (raw)": JsonMetadataValue(dag_run),
                                "Start Date": TimestampMetadataValue(
                                    timestamp_from_airflow_date(dag_run["start_date"])
                                ),
                                "End Date": TimestampMetadataValue(
                                    timestamp_from_airflow_date(dag_run["end_date"])
                                ),
                                "Run Type": dag_run["run_type"],
                                "Airflow Config": JsonMetadataValue(dag_run["conf"]),
                                "Link to Run": MarkdownMetadataValue(
                                    f"[View Run]({airflow_webserver_url}/dags/{dag_id}/grid?dag_run_id={dag_run['dag_run_id']}&tab=details)"
                                ),
                            },
                        )
                        for spec in specs
                    ]
                )
        context.update_cursor(str(current_date.timestamp()))
        return SensorResult(
            asset_events=materializations_to_report,
        )

    return airflow_dag_sensor


def timestamp_from_airflow_date(airflow_date: str) -> float:
    try:
        return datetime.datetime.strptime(airflow_date, "%Y-%m-%dT%H:%M:%S+00:00").timestamp()
    except ValueError:
        return datetime.datetime.strptime(airflow_date, "%Y-%m-%dT%H:%M:%S.%f+00:00").timestamp()


def add_prefix_to_specs(prefix: Sequence[str], specs: Sequence[AssetSpec]) -> Sequence[AssetSpec]:
    return [
        AssetSpec(
            key=AssetKey([*prefix, *spec.key.path]),
            description=spec.description,
            metadata=spec.metadata,
            tags=spec.tags,
            deps=spec.deps,
        )
        for spec in specs
    ]


# This currently assumes an entire dbt project is being munged in one dag task. Unlikely, and we should
# figure out better argument structure / being able to represent the split in the dbt project.
def airflow_task_mappings_from_dbt_project(
    dbt_manifest_path: str,
    airflow_instance_name: str,
    dag_id: str,
    task_id: str,
) -> Sequence[TaskMapping]:
    manifest = json.loads(open(dbt_manifest_path).read())
    project_name = manifest["metadata"]["project_name"]
    original_specs = build_dbt_asset_specs(manifest=manifest)
    dbt_specs = add_prefix_to_specs([airflow_instance_name, "dbt"], original_specs)
    task_mappings = []

    # This is all a bit gross but it's to map the asset key prefix to the deps correctly.
    before_prefix_asset_keys = [spec.key for spec in original_specs]
    for spec in dbt_specs:
        deps = [
            AssetDep(AssetKey([airflow_instance_name, "dbt", *dep.asset_key.path]))
            if dep.asset_key in before_prefix_asset_keys
            else dep
            for dep in spec.deps
        ]
        task_mappings.append(
            TaskMapping(
                dag_id=dag_id,
                task_id=task_id,
                key=spec.key,
                deps=deps,
                tags=spec.tags,
                metadata=spec.metadata,
                group=project_name,
            )
        )
    return task_mappings


def get_leaf_specs(specs: List[AssetSpec]) -> List[AssetSpec]:
    asset_key_to_specs = {spec.key: spec for spec in specs}
    downstreams_per_key: Dict[AssetKey, List[AssetKey]] = {}
    for spec in specs:
        # each dep represents an upstream from spec.key to dep.key. So reverse the relationship
        for dep in spec.deps:
            downstreams_per_key[dep.asset_key] = downstreams_per_key.get(dep.asset_key, []) + [
                spec.key
            ]

    # leaf asset keys are those that have no downstreams.
    leaf_specs = [
        asset_key_to_specs[key]
        for key in asset_key_to_specs.keys()
        if key not in downstreams_per_key
    ]
    return leaf_specs
