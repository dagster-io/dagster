from collections import defaultdict
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Set, Union

from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    _check as check,
    external_asset_from_spec,
)
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
from dagster._record import record
from dagster._serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_airlift.constants import AIRFLOW_SOURCE_METADATA_KEY_PREFIX
from dagster_airlift.core.airflow_instance import AirflowInstance, TaskInfo
from dagster_airlift.core.dag_asset import dag_asset_spec_data
from dagster_airlift.core.sensor import (
    DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS,
    build_airflow_polling_sensor,
)
from dagster_airlift.core.serialization_utils import (
    AssetSpecData,
    ExistingAssetKeyAirflowData,
    GenericAssetKeyMappingSerializer,
)
from dagster_airlift.core.task_asset import get_airflow_data_for_task_mapped_spec
from dagster_airlift.core.utils import get_dag_id_from_asset, get_task_id_from_asset
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
    serialized_data = _get_or_create_serialized_data(
        context, _metadata_key(airflow_instance), airflow_instance, defs
    )
    return definitions_from_metadata(
        serialized_data, defs, airflow_instance, sensor_minimum_interval_seconds
    )


def _metadata_key(airflow_instance: AirflowInstance) -> str:
    return f"{AIRFLOW_SOURCE_METADATA_KEY_PREFIX}/{airflow_instance.name}"


def _get_or_create_serialized_data(
    context: DefinitionsLoadContext,
    metadata_key: str,
    airflow_instance: AirflowInstance,
    defs: Definitions,
) -> "_SerializedData":
    if (
        context.load_type == DefinitionsLoadType.RECONSTRUCTION
        and metadata_key in context.reconstruction_metadata
    ):
        return deserialize_value(context.reconstruction_metadata[metadata_key], _SerializedData)
    else:
        return compute_serialized_data(airflow_instance=airflow_instance, defs=defs)


def compute_serialized_data(
    airflow_instance: AirflowInstance, defs: Definitions
) -> "_SerializedData":
    migration_state = airflow_instance.get_migration_state()
    dag_infos = {dag.dag_id: dag for dag in airflow_instance.list_dags()}

    # Do a pass over the passed-in definitions to compute the asset graph, the assets corresponding to tasks in each dag,
    # and additional transformations to perform to each asset spec (e.g. adding metadata).
    serializable_data = serializable_data_from_defs(
        definitions=defs,
        migration_state=migration_state,
        airflow_instance=airflow_instance,
    )

    serializable_specs = []
    # Construct serializable specs for each dag.
    for dag in dag_infos.values():
        spec = dag_asset_spec_data(
            airflow_instance=airflow_instance,
            task_asset_keys_in_dag=serializable_data.keys_in_dag.get(dag.dag_id, set()),
            downstreams_asset_dependency_graph=serializable_data.downstreams_asset_graph,
            dag_info=dag,
        )
        serializable_specs.append(spec)
        for dep in spec.deps:
            serializable_data.downstreams_asset_graph[dep.asset_key].add(dag.dag_asset_key)

    return _SerializedData(
        airflow_datas_per_existing_asset_key=serializable_data.per_existing_asset_key_airflow_data,
        new_asset_datas=serializable_specs,
    )


def definitions_from_metadata(
    definitions_metadata: "_SerializedData",
    defs: Definitions,
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
) -> Definitions:
    assets_defs = construct_all_assets(
        definitions=defs,
        serialized_data=definitions_metadata,
    )
    return defs_with_assets_and_sensor(
        defs, assets_defs, airflow_instance, sensor_minimum_interval_seconds, definitions_metadata
    )


def defs_with_assets_and_sensor(
    defs: Definitions,
    assets_defs: List[AssetsDefinition],
    airflow_instance: AirflowInstance,
    sensor_minimum_interval_seconds: int,
    definitions_metadata: "_SerializedData",
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


@whitelist_for_serdes(
    field_serializers={
        "airflow_datas_per_existing_asset_key": GenericAssetKeyMappingSerializer,
    }
)
@record
class _SerializedData:
    """Data that will be serialized and cached to avoid repeated calls to the Airflow API,
    and repeated scans of passed-in Definitions objects.
    """

    airflow_datas_per_existing_asset_key: Dict[AssetKey, "ExistingAssetKeyAirflowData"]
    new_asset_datas: Sequence[AssetSpecData]


@record
class _AirflowDataForDefs:
    """Serializable data that represents information gleaned from the passed-in Definitions object."""

    # Once over the serialization boundary, these will be combined with an original AssetSpec to create the final AssetSpec.
    # In practice, we attach task-level metadata to the AssetSpecs.
    per_existing_asset_key_airflow_data: Dict[AssetKey, ExistingAssetKeyAirflowData] = {}
    # These are the assets which map to tasks within a given dag.
    keys_in_dag: Dict[str, Set[AssetKey]] = {}
    # This is the asset dependency graph, which we use to determine the leaf assets for a given dag.
    downstreams_asset_graph: Dict[AssetKey, Set[AssetKey]] = {}


def serializable_data_from_defs(
    definitions: Definitions,
    migration_state: AirflowMigrationState,
    airflow_instance: AirflowInstance,
) -> _AirflowDataForDefs:
    """Compute data from definitions that can be cached and used to construct the "final" definitions,
    without calls to the airflow rest API.
    """
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    per_asset_key_airflow_data: Dict[AssetKey, ExistingAssetKeyAirflowData] = {}
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    for asset in definitions.assets or []:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetsDefinition, AssetSpec),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        task_info = get_task_info_for_asset(airflow_instance, asset)
        if task_info is None:
            continue
        migration_state_for_task = migration_state.get_migration_state_for_task(
            dag_id=task_info.dag_id, task_id=task_info.task_id
        )
        specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
        for spec in specs:
            per_asset_key_airflow_data[spec.key] = get_airflow_data_for_task_mapped_spec(
                task_info=task_info,
                migration_state=migration_state_for_task,
                spec=spec,
            )
            for dep in spec.deps:
                downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
            all_asset_keys_per_dag_id[task_info.dag_id].add(spec.key)
    return _AirflowDataForDefs(
        per_existing_asset_key_airflow_data=per_asset_key_airflow_data,
        keys_in_dag=all_asset_keys_per_dag_id,
        downstreams_asset_graph=downstreams_asset_dependency_graph,
    )


def construct_all_assets(
    definitions: Definitions,
    serialized_data: _SerializedData,
) -> List[AssetsDefinition]:
    return list(
        _apply_airflow_data_to_specs(
            definitions, serialized_data.airflow_datas_per_existing_asset_key
        )
    ) + list(_construct_specs_from_data(serialized_data.new_asset_datas))


def _apply_airflow_data_to_specs(
    definitions: Definitions,
    airflow_datas_per_asset_key: Mapping[AssetKey, ExistingAssetKeyAirflowData],
) -> Iterator[AssetsDefinition]:
    """Apply asset spec transformations to the asset definitions."""

    def _map_spec(spec: AssetSpec) -> AssetSpec:
        if spec.key in airflow_datas_per_asset_key:
            return airflow_datas_per_asset_key[spec.key].apply_to_spec(spec)
        return spec

    for asset in definitions.assets or []:
        asset = check.inst(  # noqa: PLW2901
            asset,
            (AssetSpec, AssetsDefinition),
            "Expected orchestrated defs to all be AssetsDefinitions or AssetSpecs.",
        )
        assets_def = (
            asset if isinstance(asset, AssetsDefinition) else external_asset_from_spec(asset)
        )
        yield assets_def.map_asset_specs(_map_spec)


def _construct_specs_from_data(
    spec_datas: Sequence[AssetSpecData],
) -> Iterator[AssetsDefinition]:
    """Construct fully qualified AssetsDefinition objects (one per spec) from serializable specs."""
    for spec_data in spec_datas:
        yield external_asset_from_spec(spec_data.to_asset_spec())


# We expect that every asset which is passed to this function has all relevant specs mapped to a task.
def get_task_info_for_asset(
    airflow_instance: AirflowInstance, asset: Union[AssetsDefinition, AssetSpec]
) -> Optional[TaskInfo]:
    task_id = get_task_id_from_asset(asset)
    dag_id = get_dag_id_from_asset(asset)
    if task_id is None or dag_id is None:
        return None
    return airflow_instance.get_task_info(dag_id, task_id)
