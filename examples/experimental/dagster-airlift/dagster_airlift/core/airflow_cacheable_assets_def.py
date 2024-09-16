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
    airflow_dag_kind_dict,
    airflow_kind_dict,
    airflow_task_kind_dict,
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
        task_infos = {
            (dag.dag_id, task.task_id): task
            for dag in dag_infos.values()
            for task in self.airflow_instance.list_tasks(dag.dag_id)
        }
        info_from_defs = get_overrides_and_dep_graph(definitions=self.defs)
        # We need to augment the asset graph structure with the additional assets that we plan on creating.
        all_asset_keys_per_dag_id = {
            dag_id: {
                *info_from_defs.all_asset_keys_per_dag_id[dag_id],
                *{
                    task_info.task_asset_key
                    for task_info in task_infos.values()
                    if task_info.dag_id == dag_id
                    and (task_info.dag_id, task_info.task_id) not in info_from_defs.task_overrides
                },
            }
            for dag_id in dag_infos.keys()
        }
        # We also need to augment the asset graph to include the new assets we'll be creating.
        # First, determine the asset keys which correspond to each task.
        all_couplings_per_asset_key = {
            **info_from_defs.couplings_per_asset_key,
            **{
                task_info.task_asset_key: [(task_info.dag_id, task_info.task_id)]
                for task_info in task_infos.values()
                if (task_info.dag_id, task_info.task_id) not in info_from_defs.task_overrides
            },
        }
        asset_keys_per_coupling: Dict[AirflowCoupling, Set[AssetKey]] = defaultdict(set)
        for asset_key, couplings in all_couplings_per_asset_key.items():
            for coupling in couplings:
                asset_keys_per_coupling[coupling].add(asset_key)

        # Add to the asset dependency graph the dependencies from the tasks to the assets.
        asset_dep_graph = info_from_defs.downstreams_asset_dependency_graph
        # Also have a distinct graph of the upstreams that come from task ids.
        task_based_upstreams: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
        for (dag_id, task_id), constituent_asset_keys in asset_keys_per_coupling.items():
            if (dag_id, task_id) in info_from_defs.task_overrides:
                continue
            else:
                asset_keys_in_upstreams = set()
                for downstream_task_id in task_infos[(dag_id, task_id)].downstream_task_ids:
                    asset_keys_in_upstreams.update(
                        asset_keys_per_coupling[(dag_id, downstream_task_id)]
                    )
                for asset_key in constituent_asset_keys:
                    asset_dep_graph[asset_key].update(asset_keys_in_upstreams)
                    for asset_key_in_upstreams in asset_keys_in_upstreams:
                        task_based_upstreams[asset_key_in_upstreams].add(asset_key)

        new_cacheable_specs_per_key = {}
        for dag in dag_infos.values():
            source_code = self.airflow_instance.get_dag_source_code(dag.metadata["file_token"])
            # Technically possible for there to be collisions in this dictionary,
            # since we don't dedupe in Definitions.merge.
            new_cacheable_specs_per_key = merge_dicts(
                new_cacheable_specs_per_key,
                get_cached_specs_for_dag(
                    asset_dep_graph=asset_dep_graph,
                    all_asset_keys_per_dag_id=all_asset_keys_per_dag_id,
                    dag_overrides=info_from_defs.dag_overrides,
                    dag_info=dag,
                    source_code=source_code,
                ),
            )
        for key, couplings in all_couplings_per_asset_key.items():
            new_cacheable_specs_per_key = merge_dicts(
                new_cacheable_specs_per_key,
                {
                    key: cached_spec_from_couplings(
                        upstreams_from_task=task_based_upstreams[key],
                        key=key,
                        couplings=couplings,
                        og_spec=info_from_defs.spec_per_key.get(key),
                        all_task_infos=task_infos,
                        migration_state=migration_state,
                    )
                },
            )
        return [
            AssetsDefinitionCacheableData(
                extra_metadata={
                    "cacheable_specs": serialize_value(
                        CacheableSpecs(
                            specs=new_cacheable_specs_per_key,
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


def cached_spec_from_couplings(
    *,
    key: AssetKey,
    og_spec: Optional[AssetSpec],
    couplings: List[AirflowCoupling],
    upstreams_from_task: Set[AssetKey],
    all_task_infos: Mapping[AirflowCoupling, TaskInfo],
    migration_state: AirflowMigrationState,
) -> CacheableAssetSpec:
    migration_state_for_asset = _get_migration_status_across_tasks(couplings, migration_state)
    metadata = build_metadata_for_spec(
        [all_task_infos[coupling] for coupling in couplings], migration_state_for_asset
    )
    if not og_spec:
        # If there's no spec, expect that there's a single task that's being mapped to this asset.
        dag_id, task_id = couplings[0]
        task_info = all_task_infos[(dag_id, task_id)]
        return _default_task_spec(
            task_info=task_info, metadata=metadata, upstream_asset_keys=upstreams_from_task
        )
    tags = airflow_task_kind_dict() if not migration_state_for_asset else {}
    if migration_state_for_asset is not None:
        tags[MIGRATED_TAG] = str(migration_state_for_asset)
    return CacheableAssetSpec.from_asset_spec(
        og_spec,
        additional_deps=[
            AssetDep.from_coercible(upstream_key) for upstream_key in upstreams_from_task
        ],
        additional_metadata=metadata,
        additional_tags=tags,
    )


def _default_task_spec(
    task_info: TaskInfo,
    metadata: Mapping[str, Any],
    upstream_asset_keys: Set[AssetKey],
) -> CacheableAssetSpec:
    return CacheableAssetSpec(
        asset_key=task_info.task_asset_key,
        description=f"A materialization corresponds to a successful run of airflow task {task_info.task_id}.",
        metadata=metadata,
        tags=airflow_kind_dict(),
        deps=[CacheableAssetDep(asset_key=key) for key in upstream_asset_keys],
        group_name=None,
    )


def get_cached_specs_for_dag(
    *,
    asset_dep_graph: Dict[AssetKey, Set[AssetKey]],
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]],
    dag_overrides: Dict[str, Dict[AssetKey, AssetSpec]],
    dag_info: DagInfo,
    source_code: str,
) -> Dict[AssetKey, CacheableAssetSpec]:
    leaf_asset_keys = get_leaf_assets_for_dag(
        asset_keys_in_dag=all_asset_keys_per_dag_id[dag_info.dag_id],
        downstreams_asset_dependency_graph=asset_dep_graph,
    )
    metadata = {
        "Dag Info (raw)": JsonMetadataValue(dag_info.metadata),
        "Link to DAG": UrlMetadataValue(dag_info.url),
        "Dag ID": dag_info.dag_id,
    }
    # Attempt to retrieve source code from the DAG.
    metadata["Source Code"] = MarkdownMetadataValue(
        f"""
```python
{source_code}
```
            """
    )

    override_assets_for_dag = dag_overrides.get(dag_info.dag_id)
    if not override_assets_for_dag:
        default_spec = _default_dag_spec(
            dag_info=dag_info, metadata=metadata, leaf_asset_keys=leaf_asset_keys
        )
        return {default_spec.asset_key: default_spec}
    return {
        key: CacheableAssetSpec.from_asset_spec(
            spec,
            additional_metadata=metadata,
            additional_deps=leaf_asset_keys,
            additional_tags=airflow_dag_kind_dict(),
        )
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
        tags=airflow_dag_kind_dict(),
        deps=[CacheableAssetDep(asset_key=key) for key in leaf_asset_keys],
        group_name=None,
    )


class _DataFromDefs:
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]]
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]]
    dag_overrides: Dict[str, Dict[AssetKey, AssetSpec]]
    spec_per_key: Dict[AssetKey, AssetSpec]
    task_overrides: Dict[AirflowCoupling, Dict[AssetKey, AssetSpec]]
    couplings_per_asset_key: Dict[AssetKey, List[AirflowCoupling]]

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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


def get_overrides_and_dep_graph(
    definitions: Definitions,
) -> _DataFromDefs:
    """From the provided definitions, finds the task and DAG overrides, and builds out a dependency graph for the assets."""
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    override_specs_per_dag_id: Dict[str, Dict[AssetKey, AssetSpec]] = defaultdict(dict)
    spec_per_key: Dict[AssetKey, AssetSpec] = {}
    couplings_per_asset_key: Dict[AssetKey, List[AirflowCoupling]] = defaultdict(list)
    override_specs_per_coupling: Dict[AirflowCoupling, Dict[AssetKey, AssetSpec]] = defaultdict(
        dict
    )
    for assets_def in definitions.get_asset_graph().assets_defs:
        for spec in assets_def.specs:
            spec_per_key[spec.key] = spec
            # First case: the spec overrides a task.
            couplings = get_couplings_from_spec(spec)
            if couplings is not None:
                # There's a way to avoid the double linear time scan here by passing the dictionary through the call stack.
                for dep in spec.deps:
                    downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
                couplings_per_asset_key[spec.key] = couplings
                for dag_id, task_id in couplings:
                    override_specs_per_coupling[(dag_id, task_id)][spec.key] = spec
                    all_asset_keys_per_dag_id[dag_id].add(spec.key)
            # Second case: the spec is a DAG asset.
            dag_id = get_dag_id_from_spec(spec)
            if dag_id is not None:
                override_specs_per_dag_id[dag_id][spec.key] = spec
    return _DataFromDefs(
        all_asset_keys_per_dag_id=all_asset_keys_per_dag_id,
        downstreams_asset_dependency_graph=downstreams_asset_dependency_graph,
        dag_overrides=override_specs_per_dag_id,
        task_overrides=override_specs_per_coupling,
        couplings_per_asset_key=couplings_per_asset_key,
        spec_per_key=spec_per_key,
    )


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
        "Dag ID": task_info.dag_id,
    }
    task_level_metadata[
        "Computed in Task ID" if bool(migration_state) is False else "Triggered by Task ID"
    ] = task_info.task_id
    return task_level_metadata
