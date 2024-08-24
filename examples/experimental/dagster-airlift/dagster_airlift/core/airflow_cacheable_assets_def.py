import hashlib
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union

from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    JsonMetadataValue,
    MarkdownMetadataValue,
    _check as check,
    multi_asset,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.loadable import (
    AssetDepRecord,
    AssetSpecRecord,
    DefLoadingContext,
    DefsRecord,
    LoadableDefs,
)
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value

from dagster_airlift.migration_state import AirflowMigrationState

from .airflow_instance import AirflowInstance, DagInfo, TaskInfo
from .utils import (
    DAG_ID_TAG,
    MIGRATED_TAG,
    TASK_ID_TAG,
    get_dag_id_from_asset,
    get_task_id_from_asset,
)

DEFAULT_POLL_INTERVAL = 60


def is_task_affined_spec(spec: AssetSpec) -> bool:
    return (spec.metadata or {}).get("airlift/airflow_artifact_type") == "task"


def is_dag_spec(spec: AssetSpec) -> bool:
    return (spec.metadata or {}).get("airlift/airflow_artifact_type") == "dag"


class LoadableAirflowInstanceDefs(LoadableDefs):
    def __init__(
        self,
        airflow_instance: AirflowInstance,
        poll_interval: int,
        defs: Optional[Definitions] = None,
        migration_state_override: Optional[AirflowMigrationState] = None,
    ):
        self.airflow_instance = airflow_instance
        self.poll_interval = poll_interval
        self.defs = defs
        self.migration_state_override = migration_state_override
        super().__init__(
            external_source_key=f"airlift/airflow_instance/{airflow_instance.normalized_name}"
        )

    def compute_defs_record(self, context: DefLoadingContext) -> DefsRecord:
        dag_infos = {dag.dag_id: dag for dag in self.airflow_instance.list_dags()}
        cacheable_task_data = construct_records_and_infer_dependencies(
            definitions=self.defs,
            migration_state=self.migration_state_override,
            airflow_instance=self.airflow_instance,
            dag_infos=dag_infos,
        )

        dag_spec_records_per_key: Dict[AssetKey, AssetSpecRecord] = {}
        for dag in dag_infos.values():
            source_code = self.airflow_instance.get_dag_source_code(dag.metadata["file_token"])
            dag_spec_records_per_key[dag.dag_asset_key] = asset_spec_record_for_dag(
                airflow_instance=self.airflow_instance,
                task_asset_keys_in_dag=cacheable_task_data.all_asset_keys_per_dag_id.get(
                    dag.dag_id, set()
                ),
                downstreams_asset_dependency_graph=cacheable_task_data.downstreams_asset_dependency_graph,
                dag_info=dag,
                source_code=source_code,
            )

        asset_spec_records = []
        asset_spec_records.extend(cacheable_task_data.spec_records_by_asset_key.values())
        asset_spec_records.extend(dag_spec_records_per_key.values())
        return DefsRecord(asset_spec_records=asset_spec_records)

    def definitions_from_record(self, defs_record: DefsRecord) -> Definitions:
        asset_specs = defs_record.to_asset_specs()

        dag_specs = [asset_spec for asset_spec in asset_specs if is_dag_spec(asset_spec)]
        task_specs = [asset_spec for asset_spec in asset_specs if is_task_affined_spec(asset_spec)]

        new_assets_defs = []
        for dag_spec in dag_specs:
            key = dag_spec.key
            dag_id = dag_spec.metadata["Dag ID"]
            new_assets_defs.append(
                build_airflow_asset_from_specs(
                    specs=[dag_spec],
                    name=key.to_user_string().replace("/", "__"),
                    tags={DAG_ID_TAG: dag_id},
                )
            )

        return Definitions(
            new_assets_defs
            + construct_assets_with_task_migration_info_applied(
                definitions=self.defs,
                task_specs=task_specs,
            )
        )




def asset_spec_record_for_dag(
    airflow_instance: AirflowInstance,
    task_asset_keys_in_dag: Set[AssetKey],
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
    dag_info: DagInfo,
    source_code: str,
) -> AssetSpecRecord:
    leaf_asset_keys = get_leaf_assets_for_dag(
        asset_keys_in_dag=task_asset_keys_in_dag,
        downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
    )
    metadata = {
        "Dag Info (raw)": JsonMetadataValue(dag_info.metadata),
        "Dag ID": dag_info.dag_id,
        "Link to DAG": MarkdownMetadataValue(f"[View DAG]({dag_info.url})"),
        "airlift/airflow_artifact_type": "dag",
    }
    # Attempt to retrieve source code from the DAG.
    metadata["Source Code"] = MarkdownMetadataValue(
        f"""
```python
{source_code}
```
            """
    )

    return AssetSpecRecord(
        key=dag_info.dag_asset_key,
        description=f"A materialization corresponds to a successful run of airflow DAG {dag_info.dag_id}.",
        metadata=metadata,
        tags={"dagster/compute_kind": "airflow", DAG_ID_TAG: dag_info.dag_id},
        deps=[AssetDepRecord(asset_key=key) for key in leaf_asset_keys],
        group_name=None,
    )


def build_airflow_asset_from_specs(
    specs: Sequence[AssetSpec], name: str, tags: Mapping[str, str]
) -> AssetsDefinition:
    @multi_asset(
        name=name,
        specs=specs,
        compute_kind="airflow",
        op_tags=tags,
    )
    def _asset(context):
        raise Exception("This should never be called.")

    return _asset


@record
class RecordsAndDependencies:
    spec_records_by_asset_key: Dict[AssetKey, AssetSpecRecord] = {}
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = {}
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = {}


def construct_records_and_infer_dependencies(
    definitions: Optional[Definitions],
    migration_state: Optional[AirflowMigrationState],
    airflow_instance: AirflowInstance,
    dag_infos: Dict[str, DagInfo],
) -> RecordsAndDependencies:
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    asset_spec_record_dict: Dict[AssetKey, AssetSpecRecord] = {}
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    if not definitions or not definitions.assets:
        return RecordsAndDependencies()

    for asset in definitions.assets:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetsDefinition, AssetSpec),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        task_info = get_task_info_for_asset(airflow_instance, asset)
        if task_info is None:
            continue
        task_level_metadata = {
            "Task Info (raw)": JsonMetadataValue(task_info.metadata),
            # In this case,
            "Dag ID": task_info.dag_id,
            "Link to DAG": MarkdownMetadataValue(f"[View DAG]({task_info.dag_url})"),
            "airlift/airflow_artifact_type": "task",
        }
        migration_state_for_task = _get_migration_state_for_task(
            migration_state_override=migration_state,
            task_info=task_info,
            dag_info=dag_infos[task_info.dag_id],
        )
        task_level_metadata[
            "Computed in Task ID" if migration_state_for_task is False else "Triggered by Task ID"
        ] = task_info.task_id
        specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
        for spec in specs:
            for dep in spec.deps:
                downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
            asset_spec_record_dict[spec.key] = AssetSpecRecord(
                key=spec.key,
                description=spec.description,
                metadata=task_level_metadata,
                tags={
                    **spec.tags,
                    MIGRATED_TAG: str(migration_state_for_task),
                    DAG_ID_TAG: task_info.dag_id,
                    TASK_ID_TAG: task_info.task_id,
                },
                deps=[AssetDepRecord(asset_key=dep.asset_key) for dep in spec.deps],
                group_name=spec.group_name,
            )
            all_asset_keys_per_dag_id[task_info.dag_id].add(spec.key)
    return RecordsAndDependencies(
        spec_records_by_asset_key=asset_spec_record_dict,
        all_asset_keys_per_dag_id=all_asset_keys_per_dag_id,
        downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
    )


def construct_assets_with_task_migration_info_applied(
    definitions: Optional[Definitions], task_specs: Sequence[AssetSpec]
) -> List[AssetsDefinition]:
    if not definitions or not definitions.assets:
        return []

    task_spec_by_key = {spec.key: spec for spec in task_specs}

    new_assets_defs = []
    for asset in definitions.assets:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        dag_id = get_dag_id_from_asset(asset)
        if dag_id is None:
            new_assets_defs.append(asset)
            continue
        overall_migration_status = None
        overall_task_id = None
        overall_dag_id = None
        new_specs = []
        specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
        for spec in specs:
            check.invariant(
                task_spec_by_key.get(spec.key) is not None,
                f"Could not find cacheable spec for asset key {spec.key.to_user_string()}",
            )
            # We allow arbitrary (non-serdes) metadata in asset specs, which makes them non-serializable.
            # This means we need to "combine" the metadata from the cacheable spec with the non-serializable
            # metadata fields from the original spec it was built from after deserializing.
            new_spec = task_spec_by_key[spec.key].with_metadata(spec.metadata)
            check.invariant(
                MIGRATED_TAG in new_spec.tags,
                f"Could not find migrated status for asset key {spec.key.to_user_string()}",
            )
            check.invariant(
                overall_migration_status is None
                or overall_migration_status == new_spec.tags[MIGRATED_TAG],
                "Expected all assets in an AssetsDefinition (and therefore the same task) to have the same migration status.",
            )
            overall_migration_status = new_spec.tags[MIGRATED_TAG]
            check.invariant(
                DAG_ID_TAG in new_spec.tags,
                f"Could not find dag ID for asset key {spec.key.to_user_string()}",
            )
            dag_id = new_spec.tags[DAG_ID_TAG]
            check.invariant(
                overall_dag_id is None or overall_dag_id == dag_id,
                "Expected all assets in an AssetsDefinition to have the same dag ID.",
            )
            overall_dag_id = dag_id
            check.invariant(
                TASK_ID_TAG in new_spec.tags,
                f"Could not find task ID for asset key {spec.key.to_user_string()}",
            )
            task_id = new_spec.tags[TASK_ID_TAG]
            check.invariant(
                overall_task_id is None or overall_task_id == task_id,
                "Expected all assets in an AssetsDefinition to have the same task ID.",
            )
            overall_task_id = task_id
            new_specs.append(new_spec)

        # We don't coerce to a bool here since bool("False") is True.
        if overall_migration_status == "True":
            asset = check.inst(  # noqa: PLW2901
                asset,
                AssetsDefinition,
                f"For an asset to be migrated, it must be an AssetsDefinition. Found an AssetSpec for task ID {task_id}.",
            )
            check.invariant(
                asset.is_executable,
                f"For an asset to be marked as migrated, it must also be executable in dagster. Found unexecutable assets for task ID {task_id}.",
            )
            new_assets_defs.append(
                AssetsDefinition(
                    keys_by_input_name=asset.keys_by_input_name,
                    keys_by_output_name=asset.keys_by_output_name,
                    node_def=asset.node_def,
                    partitions_def=asset.partitions_def,
                    specs=new_specs,
                )
            )
        else:
            new_assets_defs.append(
                build_airflow_asset_from_specs(
                    specs=new_specs,
                    name=f"{overall_dag_id}__{overall_task_id}",
                    tags=asset.node_def.tags if isinstance(asset, AssetsDefinition) else {},
                )
            )
    return new_assets_defs


# We expect that every asset which is passed to this function has all relevant specs mapped to a task.
def get_task_info_for_asset(
    airflow_instance: AirflowInstance, asset: Union[AssetsDefinition, AssetSpec]
) -> Optional[TaskInfo]:
    task_id = get_task_id_from_asset(asset)
    dag_id = get_dag_id_from_asset(asset)
    if task_id is None or dag_id is None:
        return None
    return airflow_instance.get_task_info(dag_id, task_id)


def get_leaf_assets_for_dag(
    asset_keys_in_dag: Set[AssetKey],
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
) -> List[AssetKey]:
    # An asset is a "leaf" for the dag if it has no transitive dependencies _within_ the dag. It may have
    # dependencies _outside_ the dag.
    leaf_assets = []
    cache = {}
    for asset_key in asset_keys_in_dag:
        if (
            get_transitive_dependencies_for_asset(
                asset_key, downstreams_asset_dependency_graph, cache
            ).intersection(asset_keys_in_dag)
            == set()
        ):
            leaf_assets.append(asset_key)
    return leaf_assets


def get_transitive_dependencies_for_asset(
    asset_key: AssetKey,
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
    cache: Dict[AssetKey, Set[AssetKey]],
) -> Set[AssetKey]:
    if asset_key in cache:
        return cache[asset_key]
    transitive_deps = set()
    for dep in downstreams_asset_dependency_graph[asset_key]:
        transitive_deps.add(dep)
        transitive_deps.update(
            get_transitive_dependencies_for_asset(dep, downstreams_asset_dependency_graph, cache)
        )
    cache[asset_key] = transitive_deps
    return transitive_deps


def _get_migration_state_for_task(
    migration_state_override: Optional[AirflowMigrationState],
    task_info: TaskInfo,
    dag_info: DagInfo,
) -> bool:
    task_id = task_info.task_id
    dag_id = dag_info.dag_id
    if migration_state_override:
        return migration_state_override.get_migration_state_for_task(dag_id, task_id) or False
    else:
        return dag_info.migration_state.is_task_migrated(task_id) or False
