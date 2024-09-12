import hashlib
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Union

from dagster import (
    AssetDep,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    JsonMetadataValue,
    MarkdownMetadataValue,
    _check as check,
    external_asset_from_spec,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.metadata.metadata_value import UrlMetadataValue
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster._serdes.serdes import (
    FieldSerializer,
    JsonSerializableValue,
    PackableValue,
    SerializableNonScalarKeyMapping,
    UnpackContext,
    WhitelistMap,
    pack_value,
    unpack_value,
)

from dagster_airlift.constants import (
    AIRFLOW_COUPLING_METADATA_KEY,
    DAG_ID_METADATA_KEY,
    MIGRATED_TAG,
)
from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo, TaskInfo
from dagster_airlift.core.utils import airflow_kind_dict, get_couplings_from_asset
from dagster_airlift.migration_state import AirflowMigrationState


# We serialize dictionaries as json, and json doesn't know how to serialize AssetKeys. So we wrap the mapping
# to be able to serialize this dictionary with "non scalar" keys.
class CacheableSpecMappingSerializer(FieldSerializer):
    def pack(
        self,
        mapping: Mapping[str, "CacheableAssetSpec"],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        return pack_value(SerializableNonScalarKeyMapping(mapping), whitelist_map, descent_path)

    def unpack(
        self,
        unpacked_value: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue:
        return unpack_value(unpacked_value, dict, whitelist_map, context)


@whitelist_for_serdes(
    field_serializers={
        "task_asset_specs": CacheableSpecMappingSerializer,
        "dag_asset_specs": CacheableSpecMappingSerializer,
    }
)
@record
class CacheableSpecs:
    task_asset_specs: Dict[AssetKey, "CacheableAssetSpec"]
    dag_asset_specs: Dict[AssetKey, "CacheableAssetSpec"]


@whitelist_for_serdes
@record
class CacheableAssetSpec:
    # A dumbed down version of AssetSpec that can be serialized easily to and from a dictionary.
    asset_key: AssetKey
    description: Optional[str]
    metadata: Mapping[str, Any]
    tags: Mapping[str, str]
    deps: Optional[Sequence["CacheableAssetDep"]]
    group_name: Optional[str]

    def to_asset_spec(
        self, *, additional_metadata: Mapping[str, Any] = {}, additional_tags: Dict[str, Any] = {}
    ) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            description=self.description,
            metadata={**additional_metadata, **self.metadata},
            tags={**additional_tags, **self.tags},
            deps=[AssetDep(asset=dep.asset_key) for dep in self.deps] if self.deps else [],
            group_name=self.group_name,
        )

    @staticmethod
    def from_asset_spec(asset_spec: AssetSpec) -> "CacheableAssetSpec":
        return CacheableAssetSpec(
            asset_key=asset_spec.key,
            description=asset_spec.description,
            metadata=asset_spec.metadata,
            tags=asset_spec.tags,
            deps=[CacheableAssetDep.from_asset_dep(dep) for dep in asset_spec.deps],
            group_name=asset_spec.group_name,
        )


@whitelist_for_serdes
@record
class CacheableAssetDep:
    # A dumbed down version of AssetDep that can be serialized easily to and from a dictionary.
    asset_key: AssetKey

    @staticmethod
    def from_asset_dep(asset_dep: AssetDep) -> "CacheableAssetDep":
        return CacheableAssetDep(asset_key=asset_dep.asset_key)


DEFAULT_POLL_INTERVAL = 60


class AirflowCacheableAssetsDefinition(CacheableAssetsDefinition):
    """Builds cacheable assets definitions for Airflow DAGs."""

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

    @property
    def unique_id(self) -> str:
        airflow_instance_name_hash = hashlib.md5(
            self.airflow_instance.normalized_name.encode()
        ).hexdigest()
        return f"airflow_assets_{airflow_instance_name_hash}"

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        migration_state = (
            self.migration_state_override or self.airflow_instance.get_migration_state()
        )
        dag_infos = {dag.dag_id: dag for dag in self.airflow_instance.list_dags()}
        cacheable_task_data = construct_cacheable_assets_and_infer_dependencies(
            definitions=self.defs,
            migration_state=migration_state,
            airflow_instance=self.airflow_instance,
            dag_infos=dag_infos,
        )

        dag_specs_per_key: Dict[AssetKey, CacheableAssetSpec] = {}
        for dag in dag_infos.values():
            source_code = self.airflow_instance.get_dag_source_code(dag.metadata["file_token"])
            dag_specs_per_key[dag.dag_asset_key] = get_cached_spec_for_dag(
                airflow_instance=self.airflow_instance,
                task_asset_keys_in_dag=cacheable_task_data.all_asset_keys_per_dag_id.get(
                    dag.dag_id, set()
                ),
                downstreams_asset_dependency_graph=cacheable_task_data.downstreams_asset_dependency_graph,
                dag_info=dag,
                source_code=source_code,
            )
        return [
            AssetsDefinitionCacheableData(
                extra_metadata={
                    "cacheable_specs": serialize_value(
                        CacheableSpecs(
                            task_asset_specs=cacheable_task_data.cacheable_specs_per_asset_key,
                            dag_asset_specs=dag_specs_per_key,
                        )
                    ),
                },
            )
        ]

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        check.invariant(len(data) == 1, "Expected exactly one cacheable data object.")
        metadata: Mapping[str, Any] = check.not_none(
            data[0].extra_metadata, "Expected cacheable data to have extra_metadata field set."
        )
        cacheable_specs = deserialize_value(metadata["cacheable_specs"], CacheableSpecs)

        new_assets_defs = []

        new_assets_defs.extend(
            external_asset_from_spec(
                dag_spec.to_asset_spec(additional_metadata={}),
            )
            for dag_spec in cacheable_specs.dag_asset_specs.values()
        )
        return new_assets_defs + construct_assets_with_task_migration_info_applied(
            definitions=self.defs,
            cacheable_specs=cacheable_specs,
        )


def get_cached_spec_for_dag(
    airflow_instance: AirflowInstance,
    task_asset_keys_in_dag: Set[AssetKey],
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
    dag_info: DagInfo,
    source_code: str,
) -> CacheableAssetSpec:
    leaf_asset_keys = get_leaf_assets_for_dag(
        asset_keys_in_dag=task_asset_keys_in_dag,
        downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
    )
    metadata = {
        "Dag Info (raw)": JsonMetadataValue(dag_info.metadata),
        DAG_ID_METADATA_KEY: dag_info.dag_id,
        "Link to DAG": UrlMetadataValue(dag_info.url),
    }
    # Attempt to retrieve source code from the DAG.
    metadata["Source Code"] = MarkdownMetadataValue(
        f"""
```python
{source_code}
```
            """
    )

    return CacheableAssetSpec(
        asset_key=dag_info.dag_asset_key,
        description=f"A materialization corresponds to a successful run of airflow DAG {dag_info.dag_id}.",
        metadata=metadata,
        tags=airflow_kind_dict(),
        deps=[CacheableAssetDep(asset_key=key) for key in leaf_asset_keys],
        group_name=None,
    )


@record
class _CacheableData:
    cacheable_specs_per_asset_key: Dict[AssetKey, CacheableAssetSpec] = {}
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = {}
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = {}


def _get_migration_status_from_state_across_specs(
    asset: Union[AssetsDefinition, AssetSpec], migration_state: AirflowMigrationState
) -> Optional[bool]:
    # We do this to keep things simple for now, but we should be able to relax this constraint.
    couplings = check.not_none(
        get_couplings_from_asset(asset), "Expected asset to have a task and dag ID."
    )
    migration_states_across_tasks = {
        migration_state.get_migration_state_for_task(dag_id=dag_id, task_id=task_id)
        for (dag_id, task_id) in couplings
    }
    check.invariant(
        len(migration_states_across_tasks) == 1,
        "Expected all tasks in an asset to have the same migration status.",
    )
    return next(iter(migration_states_across_tasks))


def _get_migration_status_from_tags_across_specs(
    specs: Sequence[AssetSpec],
) -> Optional[bool]:
    # We do this to keep things simple for now, but we should be able to relax this constraint.
    migration_states_across_tasks = {spec.tags.get(MIGRATED_TAG) for spec in specs}
    check.invariant(
        len(migration_states_across_tasks) == 1,
        "Expected all tasks in an asset to have the same migration status.",
    )
    migration_state = next(iter(migration_states_across_tasks))
    return migration_state == "True" if migration_state else None


def construct_cacheable_assets_and_infer_dependencies(
    definitions: Optional[Definitions],
    migration_state: AirflowMigrationState,
    airflow_instance: AirflowInstance,
    dag_infos: Dict[str, DagInfo],
) -> _CacheableData:
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    cacheable_specs_per_asset_key: Dict[AssetKey, CacheableAssetSpec] = {}
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    if not definitions or not definitions.assets:
        return _CacheableData()
    for asset in definitions.assets:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetsDefinition, AssetSpec),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        couplings = get_couplings_from_asset(asset)
        if not couplings:
            continue
        migration_state_for_asset = _get_migration_status_from_state_across_specs(
            asset, migration_state
        )
        task_infos = get_task_infos_for_asset(airflow_instance, asset)
        if not task_infos:
            continue
        metadata = build_metadata_for_asset(task_infos, migration_state_for_asset)
        specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
        for spec in specs:
            spec_deps = []
            for dep in spec.deps:
                spec_deps.append(CacheableAssetDep.from_asset_dep(dep))
                downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
            cacheable_specs_per_asset_key[spec.key] = CacheableAssetSpec(
                asset_key=spec.key,
                description=spec.description,
                metadata={
                    **metadata,
                    AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue(couplings),
                },
                tags={
                    **spec.tags,
                    MIGRATED_TAG: str(bool(migration_state_for_asset)),
                },
                deps=spec_deps,
                group_name=spec.group_name,
            )
            for dag_id, task_id in couplings:
                all_asset_keys_per_dag_id[dag_id].add(spec.key)
    return _CacheableData(
        cacheable_specs_per_asset_key=cacheable_specs_per_asset_key,
        all_asset_keys_per_dag_id=all_asset_keys_per_dag_id,
        downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
    )


def construct_assets_with_task_migration_info_applied(
    definitions: Optional[Definitions],
    cacheable_specs: CacheableSpecs,
) -> List[AssetsDefinition]:
    if not definitions or not definitions.assets:
        return []

    new_assets_defs = []
    for asset in definitions.assets:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        couplings = get_couplings_from_asset(asset)
        if couplings is None:
            # The cacheable assets abstraction can only handle returning a list of assetsdefinitions, not specs. So if specs are passed in,
            # we need to coerce them.
            if isinstance(asset, AssetSpec):
                new_assets_defs.append(external_asset_from_spec(asset))
            else:
                new_assets_defs.append(asset)
            continue
        new_specs = _verify_cacheable_and_build_spec(
            cacheable_specs.task_asset_specs,
            asset.specs if isinstance(asset, AssetsDefinition) else [asset],
        )
        overall_migration_status = _get_migration_status_from_tags_across_specs(new_specs)
        if overall_migration_status is True:
            asset = check.inst(  # noqa: PLW2901
                asset,
                AssetsDefinition,
                "For an asset to be migrated, it must be an AssetsDefinition. Found an AssetSpec.",
            )
            check.invariant(
                asset.is_executable,
                "For an asset to be marked as migrated, it must also be executable in dagster. Found unexecutable assets.",
            )
            # This is suspect. Should we not be using a full AssetsDefinition copy here.
            # https://linear.app/dagster-labs/issue/FOU-372/investigate-suspect-code-in-construct-assets-with-task-migration-info
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
            new_assets_defs.extend(external_asset_from_spec(spec) for spec in new_specs)
    return new_assets_defs


# We expect that every asset which is passed to this function has all relevant specs mapped to a task.
def get_task_infos_for_asset(
    airflow_instance: AirflowInstance, asset: Union[AssetsDefinition, AssetSpec]
) -> List[TaskInfo]:
    return [
        airflow_instance.get_task_info(dag_id, task_id)
        for (dag_id, task_id) in get_couplings_from_asset(asset) or []
    ]


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


def _verify_cacheable_and_build_spec(
    task_asset_specs: Dict[AssetKey, CacheableAssetSpec], specs: Iterable[AssetSpec]
) -> Sequence[AssetSpec]:
    overall_migration_status = None
    overall_dag_and_task_list = None
    new_specs = []
    for spec in specs:
        cacheable_spec = check.not_none(
            task_asset_specs.get(spec.key),
            f"Could not find cacheable spec for asset key {spec.key.to_user_string()}",
        )

        check.invariant(
            MIGRATED_TAG in cacheable_spec.tags,
            f"Could not find migrated status for asset key {spec.key.to_user_string()}",
        )
        check.invariant(
            overall_migration_status is None
            or overall_migration_status == cacheable_spec.tags[MIGRATED_TAG],
            "Expected all assets in an AssetsDefinition (and therefore the same task) to have the same migration status.",
        )
        overall_migration_status = cacheable_spec.tags[MIGRATED_TAG]
        dag_and_task_list = cacheable_spec.metadata[AIRFLOW_COUPLING_METADATA_KEY]
        check.invariant(
            overall_dag_and_task_list is None or overall_dag_and_task_list == dag_and_task_list,
            "Expected all assets in an AssetsDefinition to have the same dag ID.",
        )
        tags = {
            **spec.tags,
            MIGRATED_TAG: cacheable_spec.tags[MIGRATED_TAG],
            **(airflow_kind_dict() if overall_migration_status != "True" else {}),
        }
        overall_dag_and_task_list = dag_and_task_list
        new_specs.append(
            cacheable_spec.to_asset_spec(
                additional_metadata=spec.metadata,
                additional_tags=tags,
            )
        )
    return new_specs


def build_metadata_for_asset(
    task_infos: Sequence[TaskInfo], migration_state: Optional[bool]
) -> Dict[str, Any]:
    if len(task_infos) == 1:
        return build_singular_task_metadata(task_infos[0], migration_state)

    return {
        # When there are multiple tasks mapped to a single asset, we default to just sending all the raw metadata.
        # We key the metadata by dag_id/task_id (since we can't key by tuple in json).
        "Task Info (raw)": JsonMetadataValue(
            {
                f"{task_info.dag_id}/{task_info.task_id}": task_info.metadata
                for task_info in task_infos
            }
        ),
    }


def build_singular_task_metadata(
    task_info: TaskInfo, migration_state: Optional[bool]
) -> Dict[str, Any]:
    task_level_metadata = {
        "Task Info (raw)": JsonMetadataValue(task_info.metadata),
        # In this case,
        DAG_ID_METADATA_KEY: task_info.dag_id,
        "Link to DAG": UrlMetadataValue(task_info.dag_url),
        "Task ID": task_info.task_id,
    }
    task_level_metadata[
        "Computed in Task ID" if bool(migration_state) is False else "Triggered by Task ID"
    ] = task_info.task_id
    return task_level_metadata
