import datetime
import json
from abc import ABC
from datetime import timedelta
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence

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
from dagster._core.utils import toposort_flatten
from dagster._time import datetime_from_timestamp, get_current_datetime, get_current_timestamp
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


class AirflowAuthBackend(ABC):
    def get_session(self) -> requests.Session:
        raise NotImplementedError("This method must be implemented by subclasses.")

    def get_webserver_url(self) -> str:
        raise NotImplementedError("This method must be implemented by subclasses.")


class BasicAuthBackend(AirflowAuthBackend):
    def __init__(self, webserver_url: str, username: str, password: str):
        self._webserver_url = webserver_url
        self.username = username
        self.password = password

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = (self.username, self.password)
        return session

    def get_webserver_url(self) -> str:
        return self._webserver_url


class AirflowInstance(NamedTuple):
    auth_backend: AirflowAuthBackend
    name: str

    @property
    def normalized_name(self) -> str:
        return self.name.replace(" ", "_").replace("-", "_")

    def get_api_url(self) -> str:
        return f"{self.auth_backend.get_webserver_url()}/api/v1"

    def list_dags(self) -> List[DagInfo]:
        response = self.auth_backend.get_session().get(f"{self.get_api_url()}/dags")
        if response.status_code == 200:
            dags = response.json()
            return [
                DagInfo(
                    dag_id=dag["dag_id"],
                    metadata=dag,
                )
                for dag in dags["dags"]
            ]
        else:
            raise Exception(
                f"Failed to fetch DAGs. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_task_info(self, dag_id: str, task_id: str) -> Dict[str, Any]:
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dags/{dag_id}/tasks/{task_id}"
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Failed to fetch task info for {dag_id}/{task_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_task_url(self, dag_id: str, task_id: str) -> str:
        return f"{self.auth_backend.get_webserver_url()}/dags/{dag_id}/{task_id}"

    def get_dag_url(self, dag_id: str) -> str:
        return f"{self.auth_backend.get_webserver_url()}/dags/{dag_id}"

    def get_dag_run_url(self, dag_id: str, run_id: str) -> str:
        return f"{self.auth_backend.get_webserver_url()}/dags/{dag_id}/grid?dag_run_id={run_id}&tab=details"

    def get_dag_run_asset_key(self, dag_id: str) -> AssetKey:
        return AssetKey([self.normalized_name, "dag", f"{dag_id}__successful_run"])

    def get_dag_source_code(self, file_token: str) -> str:
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dagSources/{file_token}"
        )
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(
                f"Failed to fetch source code for {file_token}. Status code: {response.status_code}, Message: {response.text}"
            )

    @staticmethod
    def airflow_str_from_datetime(dt: datetime.datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def get_dag_runs(
        self, dag_id: str, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> List[Dict[str, Any]]:
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dags/{dag_id}/dagRuns",
            params={
                "updated_at_gte": self.airflow_str_from_datetime(start_date),
                "updated_at_lte": self.airflow_str_from_datetime(end_date),
            },
        )
        if response.status_code == 200:
            return response.json()["dag_runs"]
        else:
            raise Exception(
                f"Failed to fetch dag runs for {dag_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    @staticmethod
    def timestamp_from_airflow_date(airflow_date: str) -> float:
        try:
            return datetime.datetime.strptime(airflow_date, "%Y-%m-%dT%H:%M:%S+00:00").timestamp()
        except ValueError:
            return datetime.datetime.strptime(
                airflow_date, "%Y-%m-%dT%H:%M:%S.%f+00:00"
            ).timestamp()


def assets_defs_from_airflow_instance(
    airflow_instance: AirflowInstance,
    task_maps: Sequence[TaskMapping] = [],
) -> List[AssetsDefinition]:
    dag_infos = airflow_instance.list_dags()

    asset_specs = []

    # All the assets which map to tasks within a given dag should be considered "upstream" of the dag.
    dag_id_to_upstream_specs: Dict[str, List[AssetSpec]] = {}

    for task in task_maps:
        task_info = airflow_instance.get_task_info(task.dag_id, task.task_id)
        joined_metadata = {
            **task.metadata,
            **{
                "Task Info (raw)": JsonMetadataValue(task_info),
                "Task ID": task.task_id,
                "Dag ID": task.dag_id,
                "Link to Task": MarkdownMetadataValue(
                    f"[View Task]({airflow_instance.get_task_url(task.dag_id, task.task_id)})"
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
        dag_id_to_upstream_specs[task.dag_id] = dag_id_to_upstream_specs.get(task.dag_id, []) + [
            asset_spec
        ]

    dag_id_to_asset_key: Dict[str, AssetKey] = {}

    for dag_info in dag_infos:
        dag_id_to_asset_key[dag_info.dag_id] = airflow_instance.get_dag_run_asset_key(
            dag_info.dag_id
        )
        metadata = {
            "Dag Info (raw)": JsonMetadataValue(dag_info.metadata),
            "Dag ID": dag_info.dag_id,
            "Link to DAG": MarkdownMetadataValue(
                f"[View DAG]({airflow_instance.get_dag_url(dag_info.dag_id)})"
            ),
        }
        # Attempt to retrieve source code from the DAG.
        metadata["Source Code"] = MarkdownMetadataValue(
            f"""
```python
{airflow_instance.get_dag_source_code(dag_info.metadata["file_token"])}
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
                group_name=f"{airflow_instance.normalized_name}__dags",
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
    airflow_instance: AirflowInstance,
    airflow_asset_specs: List[AssetSpec],
) -> SensorDefinition:
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
            # For now, we materialize assets representing tasks only when the whole dag completes.
            # With a more robust cursor that can let us know when we've seen a particular task run already, then we can relax this constraint.
            for dag_run in airflow_instance.get_dag_runs(dag, last_effective_date, current_date):
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
                                    airflow_instance.timestamp_from_airflow_date(
                                        dag_run["start_date"]
                                    )
                                ),
                                "End Date": TimestampMetadataValue(
                                    airflow_instance.timestamp_from_airflow_date(
                                        dag_run["end_date"]
                                    )
                                ),
                                "Run Type": dag_run["run_type"],
                                "Airflow Config": JsonMetadataValue(dag_run["conf"]),
                                "Link to Run": MarkdownMetadataValue(
                                    f"[View Run]({airflow_instance.get_dag_run_url(dag, dag_run['dag_run_id'])})"
                                ),
                                "Creation Timestamp": TimestampMetadataValue(
                                    get_current_timestamp()
                                ),
                            },
                        )
                        for spec in toposort_specs(specs)
                    ]
                )
        context.update_cursor(str(current_date.timestamp()))
        return SensorResult(
            asset_events=materializations_to_report,
        )

    return airflow_dag_sensor


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


def toposort_specs(specs: List[AssetSpec]) -> List[AssetSpec]:
    spec_per_key = {spec.key: spec for spec in specs}
    return [
        spec_per_key[key]
        for key in toposort_flatten(
            {spec.key: {dep.asset_key for dep in spec.deps} for spec in specs}
        )
    ]
