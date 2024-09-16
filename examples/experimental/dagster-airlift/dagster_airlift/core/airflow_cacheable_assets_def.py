import hashlib
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

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
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
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
from dagster._utils.merger import merge_dicts

from dagster_airlift.constants import DAG_ID_METADATA_KEY, MIGRATED_TAG, AirflowCoupling
from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo, TaskInfo
from dagster_airlift.core.utils import (
    airflow_kind_dict,
    get_couplings_from_spec,
    get_dag_id_from_spec,
)
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
        "specs": CacheableSpecMappingSerializer,
    }
)
@record
class CacheableSpecs:
    specs: Mapping[AssetKey, "CacheableAssetSpec"]


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

    def to_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            description=self.description,
            metadata=self.metadata,
            tags=self.tags,
            deps=[AssetDep(asset=dep.asset_key) for dep in self.deps] if self.deps else [],
            group_name=self.group_name,
        )

    @staticmethod
    def from_asset_spec(
        asset_spec: AssetSpec,
        additional_deps: Sequence[CoercibleToAssetDep] = [],
        additional_tags: Dict[str, Any] = {},
        additional_metadata: Mapping[str, Any] = {},
    ) -> "CacheableAssetSpec":
        return CacheableAssetSpec(
            asset_key=asset_spec.key,
            description=asset_spec.description,
            metadata=merge_dicts(asset_spec.metadata, additional_metadata),
            tags=merge_dicts(asset_spec.tags, additional_tags),
            deps=[CacheableAssetDep.from_asset_dep(dep) for dep in asset_spec.deps]
            + [
                CacheableAssetDep.from_asset_dep(AssetDep.from_coercible(dep))
                for dep in additional_deps
            ],
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
        defs: Definitions,
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
        cacheable_data_from_provided_defs = construct_cacheable_assets_and_infer_dependencies(
            definitions=self.defs,
            migration_state=migration_state,
            airflow_instance=self.airflow_instance,
        )

        dag_specs_per_key: Dict[AssetKey, CacheableAssetSpec] = {}
        for dag in dag_infos.values():
            source_code = self.airflow_instance.get_dag_source_code(dag.metadata["file_token"])
            # Technically possible for there to be collisions in this dictionary,
            # since we don't dedupe in Definitions.merge.
            dag_specs_per_key = merge_dicts(
                dag_specs_per_key,
                get_cached_specs_for_dag(
                    cacheable_data=cacheable_data_from_provided_defs,
                    dag_info=dag,
                    source_code=source_code,
                ),
            )
        all_cacheable_specs = merge_dicts(
            cacheable_data_from_provided_defs.cacheable_specs_per_asset_key,
            dag_specs_per_key,
        )
        return [
            AssetsDefinitionCacheableData(
                extra_metadata={
                    "cacheable_specs": serialize_value(
                        CacheableSpecs(
                            specs=all_cacheable_specs,
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
        used_asset_keys = set()
        cacheable_specs = deserialize_value(metadata["cacheable_specs"], CacheableSpecs)

        def _new_up_asset(spec: AssetSpec) -> AssetSpec:
            used_asset_keys.add(spec.key)
            if spec.key in cacheable_specs.specs:
                return cacheable_specs.specs[spec.key].to_asset_spec()
            return spec

        new_assets_defs = [
            assets_def.map_asset_specs(_new_up_asset)
            for assets_def in self.defs.get_asset_graph().assets_defs
            if len(assets_def.keys) > 0
        ]
        additional_assets_defs = [
            external_asset_from_spec(spec.to_asset_spec())
            for spec in cacheable_specs.specs.values()
            if spec.asset_key not in used_asset_keys
        ]

        return new_assets_defs + additional_assets_defs


def get_cached_specs_for_dag(
    cacheable_data: "_CacheableData",
    dag_info: DagInfo,
    source_code: str,
) -> Dict[AssetKey, CacheableAssetSpec]:
    leaf_asset_keys = get_leaf_assets_for_dag(
        asset_keys_in_dag=cacheable_data.all_asset_keys_per_dag_id[dag_info.dag_id],
        downstreams_asset_dependency_graph=cacheable_data.downstreams_asset_dependency_graph,
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

    override_assets_for_dag = cacheable_data.dag_overrides.get(dag_info.dag_id)
    if not override_assets_for_dag:
        default_spec = _default_dag_spec(
            dag_info=dag_info, metadata=metadata, leaf_asset_keys=leaf_asset_keys
        )
        return {default_spec.asset_key: default_spec}
    return {
        key: CacheableAssetSpec.from_asset_spec(spec)
        for key, spec in override_assets_for_dag.items()
    }


def _default_dag_spec(
    *,
    dag_info: DagInfo,
    metadata: Mapping[str, Any],
    leaf_asset_keys: Sequence[AssetKey],
) -> CacheableAssetSpec:
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
    dag_overrides: Dict[str, Dict[AssetKey, AssetSpec]] = {}


def _get_migration_status_across_tasks(
    couplings: List[AirflowCoupling], migration_state: AirflowMigrationState
) -> Optional[bool]:
    migration_states_across_tasks = {
        migration_state.get_migration_state_for_task(dag_id=dag_id, task_id=task_id)
        for (dag_id, task_id) in couplings
    }
    check.invariant(
        len(migration_states_across_tasks) == 1,
        "Expected all tasks in an asset to have the same migration status.",
    )
    return next(iter(migration_states_across_tasks))


def construct_cacheable_assets_and_infer_dependencies(
    definitions: Optional[Definitions],
    migration_state: AirflowMigrationState,
    airflow_instance: AirflowInstance,
) -> _CacheableData:
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    cacheable_specs_per_asset_key: Dict[AssetKey, CacheableAssetSpec] = {}
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    override_specs_per_dag_id: Dict[str, Dict[AssetKey, AssetSpec]] = defaultdict(dict)
    if not definitions or not definitions.assets:
        return _CacheableData()
    for assets_def in definitions.get_asset_graph().assets_defs:
        # Skip assets which have no keys, since they represent checks.
        if not assets_def.keys:
            continue
        for spec in assets_def.specs:
            # First case: the spec overrides a task.
            couplings = get_couplings_from_spec(spec)
            if couplings is not None:
                # There's a way to avoid the double linear time scan here by passing the dictionary through the call stack.
                for dep in spec.deps:
                    downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
                cacheable_specs_per_asset_key[spec.key] = build_cacheable_spec_with_task_data(
                    spec=spec,
                    airflow_instance=airflow_instance,
                    dag_and_task_id_list=couplings,
                    migration_state=migration_state,
                )
                for dag_id, _ in couplings:
                    all_asset_keys_per_dag_id[dag_id].add(spec.key)
            # Second case: the spec is a DAG asset.
            dag_id = get_dag_id_from_spec(spec)
            # We can't build the dag spec yet, since we don't have the completed asset graph
            # (and thus, cannot infer dependencies). Instead, accumulate the assetspec in a
            # dict of overrides.
            if dag_id is not None:
                override_specs_per_dag_id[dag_id][spec.key] = spec
    return _CacheableData(
        cacheable_specs_per_asset_key=cacheable_specs_per_asset_key,
        all_asset_keys_per_dag_id=all_asset_keys_per_dag_id,
        downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
        dag_overrides=override_specs_per_dag_id,
    )


def build_cacheable_spec_with_task_data(
    *,
    spec: AssetSpec,
    airflow_instance: AirflowInstance,
    dag_and_task_id_list: List[AirflowCoupling],
    migration_state: AirflowMigrationState,
) -> CacheableAssetSpec:
    migration_state_for_asset = _get_migration_status_across_tasks(
        dag_and_task_id_list, migration_state
    )
    task_infos = get_task_infos_for_spec(airflow_instance, spec)
    metadata = build_metadata_for_spec(task_infos, migration_state_for_asset)
    tags = airflow_kind_dict() if migration_state_for_asset else {}
    if migration_state_for_asset is not None:
        tags[MIGRATED_TAG] = str(bool(migration_state_for_asset))
    return CacheableAssetSpec.from_asset_spec(
        spec, additional_metadata=metadata, additional_tags=tags
    )


# We expect that every asset which is passed to this function has all relevant specs mapped to a task.
def get_task_infos_for_spec(airflow_instance: AirflowInstance, spec: AssetSpec) -> List[TaskInfo]:
    return [
        airflow_instance.get_task_info(dag_id, task_id)
        for (dag_id, task_id) in get_couplings_from_spec(spec) or []
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


def build_metadata_for_spec(
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
