from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union

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
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
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
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airlift.constants import (
    AIRFLOW_SOURCE_METADATA_KEY_PREFIX,
    DAG_ID_METADATA_KEY,
    MIGRATED_TAG,
    TASK_ID_METADATA_KEY,
)
from dagster_airlift.core.airflow_instance import AirflowInstance, DagInfo, TaskInfo
from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor,
)
from dagster_airlift.core.utils import (
    airflow_kind_dict,
    get_dag_id_from_asset,
    get_task_id_from_asset,
)
from dagster_airlift.migration_state import AirflowMigrationState


@suppress_dagster_warnings
def build_defs_from_airflow_instance(
    *,
    airflow_instance: AirflowInstance,
    defs: Optional[Definitions] = None,
    sensor_minimum_interval_seconds: int = DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
) -> Definitions:
    defs = defs or Definitions()
    context = DefinitionsLoadContext.get()
    definitions_metadata = _get_or_create_definitions_metadata(
        context, _metadata_key(airflow_instance), airflow_instance, defs
    )
    return definitions_from_metadata(
        context, definitions_metadata, defs, airflow_instance, sensor_minimum_interval_seconds
    )


def _metadata_key(airflow_instance: AirflowInstance) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{airflow_instance.name}"


def _get_or_create_definitions_metadata(
    context: DefinitionsLoadContext,
    metadata_key: str,
    airflow_instance: AirflowInstance,
    defs: Definitions,
) -> "CacheableSpecs":
    if (
        context.load_type == DefinitionsLoadType.RECONSTRUCTION
        and metadata_key in context.reconstruction_metadata
    ):
        return deserialize_value(context.reconstruction_metadata[metadata_key], CacheableSpecs)
    else:
        return compute_cacheable_assets(airflow_instance=airflow_instance, defs=defs)


def compute_cacheable_assets(
    airflow_instance: AirflowInstance, defs: Definitions
) -> "CacheableSpecs":
    migration_state = airflow_instance.get_migration_state()
    dag_infos = {dag.dag_id: dag for dag in airflow_instance.list_dags()}
    cacheable_task_data = construct_cacheable_assets_and_infer_dependencies(
        definitions=defs,
        migration_state=migration_state,
        airflow_instance=airflow_instance,
        dag_infos=dag_infos,
    )

    cacheable_dag_spec_per_key: Dict[AssetKey, CacheableAssetSpec] = {}
    for dag in dag_infos.values():
        source_code = airflow_instance.get_dag_source_code(dag.metadata["file_token"])
        cacheable_dag_spec_per_key[dag.dag_asset_key] = get_cached_spec_for_dag(
            airflow_instance=airflow_instance,
            task_asset_keys_in_dag=cacheable_task_data.all_asset_keys_per_dag_id.get(
                dag.dag_id, set()
            ),
            downstreams_asset_dependency_graph=cacheable_task_data.downstreams_asset_dependency_graph,
            dag_info=dag,
            source_code=source_code,
        )
    return CacheableSpecs(
        dag_cacheable_asset_specs=cacheable_dag_spec_per_key,
        task_cacheable_asset_specs=cacheable_task_data.cacheable_specs_per_asset_key,
    )


def definitions_from_metadata(
    context: DefinitionsLoadContext,
    definitions_metadata: "CacheableSpecs",
    defs: Definitions,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
) -> Definitions:
    new_assets_defs = [
        external_asset_from_spec(
            cacheable_dag_spec.to_asset_spec(additional_metadata={}),
        )
        for cacheable_dag_spec in definitions_metadata.dag_cacheable_asset_specs.values()
    ]
    assets_defs = new_assets_defs + construct_assets_with_task_migration_info_applied(
        definitions=defs,
        cacheable_specs=definitions_metadata,
    )
    return defs_with_assets_and_sensor(
        defs, assets_defs, airflow_instance, sensor_minimum_interval_seconds, definitions_metadata
    )


def defs_with_assets_and_sensor(
    defs: Definitions,
    assets_defs: List[AssetsDefinition],
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
    definitions_metadata: "CacheableSpecs",
) -> Definitions:
    airflow_sensor = build_airflow_polling_sensor(
        airflow_instance=airflow_instance, minimum_interval_seconds=sensor_minimum_interval_seconds
    )
    return Definitions(
        assets=assets_defs,
        asset_checks=defs.asset_checks if defs else None,
        sensors=[airflow_sensor, *defs.sensors] if defs and defs.sensors else [airflow_sensor],
        schedules=defs.schedules if defs else None,
        jobs=defs.jobs if defs else None,
        executor=defs.executor if defs else None,
        loggers=defs.loggers if defs else None,
        resources=defs.resources if defs else None,
    ).with_reconstruction_metadata(
        {_metadata_key(airflow_instance): serialize_value(definitions_metadata)}
    )


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
        "task_cacheable_asset_specs": CacheableSpecMappingSerializer,
        "dag_cacheable_asset_specs": CacheableSpecMappingSerializer,
    }
)
@record
class CacheableSpecs:
    task_cacheable_asset_specs: Dict[AssetKey, "CacheableAssetSpec"]
    dag_cacheable_asset_specs: Dict[AssetKey, "CacheableAssetSpec"]


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
        "Dag ID": dag_info.dag_id,
        "Link to DAG": UrlMetadataValue(dag_info.url),
        DAG_ID_METADATA_KEY: dag_info.dag_id,
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
        task_info = get_task_info_for_asset(airflow_instance, asset)
        if task_info is None:
            continue
        task_level_metadata = {
            "Task Info (raw)": JsonMetadataValue(task_info.metadata),
            # In this case,
            "Dag ID": task_info.dag_id,
            "Link to DAG": UrlMetadataValue(task_info.dag_url),
        }
        migration_state_for_task = migration_state.get_migration_state_for_task(
            dag_id=task_info.dag_id, task_id=task_info.task_id
        )
        task_level_metadata[
            "Computed in Task ID" if migration_state_for_task is False else "Triggered by Task ID"
        ] = task_info.task_id
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
                    DAG_ID_METADATA_KEY: task_info.dag_id,
                    TASK_ID_METADATA_KEY: task_info.task_id,
                    **task_level_metadata,
                },
                tags={
                    **spec.tags,
                    MIGRATED_TAG: str(bool(migration_state_for_task)),
                },
                deps=spec_deps,
                group_name=spec.group_name,
            )
            all_asset_keys_per_dag_id[task_info.dag_id].add(spec.key)
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
        dag_id = get_dag_id_from_asset(asset)
        if dag_id is None:
            # The cacheable assets abstraction can only handle returning a list of assetsdefinitions, not specs. So if specs are passed in,
            # we need to coerce them.
            if isinstance(asset, AssetSpec):
                new_assets_defs.append(external_asset_from_spec(asset))
            else:
                new_assets_defs.append(asset)
            continue
        overall_migration_status = None
        overall_task_id = None
        overall_dag_id = None
        new_specs = []
        specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
        for spec in specs:
            cacheable_spec = check.not_none(
                cacheable_specs.task_cacheable_asset_specs.get(spec.key),
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
            check.invariant(
                DAG_ID_METADATA_KEY in cacheable_spec.metadata,
                f"Could not find dag ID for asset key {spec.key.to_user_string()}",
            )
            dag_id = cacheable_spec.metadata[DAG_ID_METADATA_KEY]
            check.invariant(
                overall_dag_id is None or overall_dag_id == dag_id,
                "Expected all assets in an AssetsDefinition to have the same dag ID.",
            )
            overall_dag_id = dag_id
            check.invariant(
                TASK_ID_METADATA_KEY in cacheable_spec.metadata,
                f"Could not find task ID for asset key {cacheable_spec.asset_key.to_user_string()}",
            )
            task_id = cacheable_spec.metadata[TASK_ID_METADATA_KEY]
            check.invariant(
                overall_task_id is None or overall_task_id == task_id,
                f"Expected all assets in an AssetsDefinition to have the same task ID. Found {overall_task_id} and {task_id}.",
            )
            overall_task_id = task_id

        # We don't coerce to a bool here since bool("False") is True.
        new_specs = [
            # We allow arbitrary (non-serdes) metadata in asset specs, which makes them non-serializable.
            # This means we need to "combine" the metadata from the cacheable spec with the non-serializable
            # metadata fields from the original spec it was built from after deserializing.
            cacheable_specs.task_cacheable_asset_specs[spec.key].to_asset_spec(
                additional_metadata=spec.metadata,
                additional_tags=airflow_kind_dict() if overall_migration_status != "True" else {},
            )
            for spec in specs
        ]
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
            # This is suspect. Should we not be using a full AssetsDefinition copy here.
            # https://linear.app/dagster-labs/issue/FOU-372/investigate-suspect-code-in-construct-assets-with-task-migration-info
            new_assets_defs.append(
                AssetsDefinition(
                    keys_by_input_name=asset.keys_by_input_name,
                    keys_by_output_name=asset.keys_by_output_name,
                    node_def=asset.node_def,
                    partitions_def=asset.partitions_def,
                    specs=[
                        # We allow arbitrary (non-serdes) metadata in asset specs, which makes them non-serializable.
                        # This means we need to "combine" the metadata from the cacheable spec with the non-serializable
                        # metadata fields from the original spec it was built from after deserializing.
                        cacheable_specs.task_cacheable_asset_specs[spec.key].to_asset_spec(
                            additional_metadata=spec.metadata
                        )
                        for spec in specs
                    ],
                )
            )
        else:
            new_assets_defs.extend(external_asset_from_spec(spec) for spec in new_specs)
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
