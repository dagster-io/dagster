from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, Sequence, Set, Union, cast

from dagster import (
    AssetDep,
    AssetKey,
    AssetMaterialization,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    JsonMetadataValue,
    MarkdownMetadataValue,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    TimestampMetadataValue,
    _check as check,
    multi_asset,
    sensor,
)
from dagster._core.utils import toposort_flatten
from dagster._time import datetime_from_timestamp, get_current_datetime, get_current_timestamp

from .airflow_instance import AirflowInstance, TaskInfo
from .migration_state import AirflowMigrationState


def create_defs_from_airflow_instance(
    airflow_instance: AirflowInstance,
    orchestrated_defs: Optional[Definitions] = None,
    # This parameter will go away once we can derive the migration state from airflow itself, using our built in utilities.
    # Alternatively, we can keep it around to let people override the migration state if they want.
    migration_state_override: Optional[AirflowMigrationState] = None,
) -> Definitions:
    # For each AssetsDefinition, we need to figure out the relevant migration state for that asset.
    all_asset_keys_per_dag_id: Dict[str, Set[AssetKey]] = defaultdict(set)
    # The upstream dependencies for each asset key.
    upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
    specs_by_dag_and_task_id: Dict[str, Dict[str, AssetSpec]] = defaultdict(dict)
    replaced_defs = []
    if orchestrated_defs and orchestrated_defs.assets:
        orig_resources = orchestrated_defs.resources
        migration_state = check.not_none(
            migration_state_override,
            "For now, we need to provide a migration state override if we're providing orchestrated_defs.",
        )
        for asset in orchestrated_defs.assets:
            check.invariant(
                isinstance(asset, (AssetsDefinition, AssetSpec)),
                "Expected asset to be an AssetsDefinition or AssetSpec",
            )
            correctly_typed_asset = cast(Union[AssetsDefinition, AssetSpec], asset)
            task_info = get_task_info_for_asset(airflow_instance, correctly_typed_asset)

            task_level_metadata = {
                "Task Info (raw)": JsonMetadataValue(task_info.metadata),
                # In this case,
                "Dag ID": task_info.dag_id,
                "Link to Task": MarkdownMetadataValue(
                    f"[View Task]({airflow_instance.get_task_url(task_info.dag_id, task_info.task_id)})"
                ),
            }
            # Since we want it to be possible for assets to have cross-dag dependencies (the global asset graph
            # might have dependencies irrespective of dag), we'll have a somewhat complicated pattern for figuring out
            # the leaf assets in each dag.
            if (
                migration_state.get_migration_state_for_task(task_info.dag_id, task_info.task_id)
                is True
            ):
                # Are there cases in airflow for which we'd want to relax this constraint?
                check.invariant(
                    isinstance(correctly_typed_asset, AssetsDefinition),
                    "If an asset is migrated, its compute function must exist in dagster.",
                )
                assets_def = cast(AssetsDefinition, correctly_typed_asset)
                new_specs = []
                check.invariant(
                    assets_def.is_executable, "If an asset is migrated, it must be executable."
                )
                # For all specs in the assets def, we will create new specs with task-level metadata.
                # We will also build up a dictionary representing the global asset dependency, as well as all the asset keys
                # present in each dag.
                for spec in assets_def.specs:
                    all_asset_keys_per_dag_id[task_info.dag_id].add(spec.key)
                    for dep in spec.deps:
                        downstreams_asset_dependency_graph[dep.asset_key].add(spec.key)
                        upstreams_asset_dependency_graph[spec.key].add(dep.asset_key)
                    new_specs.append(
                        AssetSpec(
                            key=spec.key,
                            description=spec.description,
                            metadata={
                                **spec.metadata,
                                **task_level_metadata,
                                "Migrated": True,
                                "Instigated by Task ID": task_info.task_id,
                            },
                            tags={**spec.tags},
                            deps=spec.deps,
                            group_name=spec.group_name,
                        )
                    )
                # We then use those new specs to construct a new AssetsDefinition.
                # We explicitly don't include the airflow compute kind tag here, because we want to be able to
                # distinguish between assets that are migrated and those that are not.
                new_assets_def = AssetsDefinition(
                    keys_by_input_name=assets_def.keys_by_input_name,
                    keys_by_output_name=assets_def.keys_by_output_name,
                    node_def=assets_def.node_def,
                    # Figuring out how to handle partitions def will be interesting/difficult.
                    partitions_def=assets_def.partitions_def,
                    specs=new_specs,
                )
                replaced_defs.append(new_assets_def)
            # In the case of an unmigrated asset spec, we will just add the metadata to each asset spec.
            # In the case of an unmigrated assets def, we will rip off the asset specs.
            # In both cases we'll actually need to construct a dummy multi asset so that we can get the compute kind.
            # Either way, update our dependency information.
            else:
                orig_asset_specs: List[AssetSpec] = (
                    [correctly_typed_asset]
                    if isinstance(correctly_typed_asset, AssetSpec)
                    else list(correctly_typed_asset.specs)
                )
                new_asset_specs = []
                for asset_spec in orig_asset_specs:
                    new_spec = AssetSpec(
                        key=asset_spec.key,
                        description=asset_spec.description,
                        metadata={
                            **asset_spec.metadata,
                            **task_level_metadata,
                            "Migrated": False,
                            "Computed in Task ID": task_info.task_id,
                        },
                        tags={**asset_spec.tags},
                        deps=asset_spec.deps,
                        group_name=asset_spec.group_name,
                    )
                    new_asset_specs.append(new_spec)
                    all_asset_keys_per_dag_id[task_info.dag_id].add(asset_spec.key)
                    for dep in asset_spec.deps:
                        downstreams_asset_dependency_graph[dep.asset_key].add(asset_spec.key)
                        upstreams_asset_dependency_graph[asset_spec.key].add(dep.asset_key)
                    specs_by_dag_and_task_id[task_info.dag_id][task_info.task_id] = new_spec

                @multi_asset(
                    specs=new_asset_specs,
                    name=f"{task_info.dag_id}__{task_info.task_id}",
                    compute_kind="airflow",
                )
                def _dummy_asset():
                    raise NotImplementedError(
                        "This is a placeholder function that should never be called."
                    )

                replaced_defs.append(_dummy_asset)
    # Now that we've replaced all the assets in the orchestrated_defs, we can build the asset specs for the dags.
    dag_id_to_assets_defs = peer_dags(
        airflow_instance,
        {
            dag_id: get_leaf_assets_for_dag(
                all_asset_keys_per_dag_id[dag_id], downstreams_asset_dependency_graph
            )
            for dag_id in all_asset_keys_per_dag_id.keys()
        },
    )
    # Now, we construct the sensor that will poll airflow for dag runs.
    airflow_sensor = build_airflow_polling_sensor(
        airflow_instance=airflow_instance,
        peered_dag_assets_defs=dag_id_to_assets_defs,
        peered_task_specs=specs_by_dag_and_task_id,
        upstreams_asset_dependency_graph=upstreams_asset_dependency_graph,
    )
    return Definitions(
        assets=[*replaced_defs, *dag_id_to_assets_defs.values()],
        sensors=[airflow_sensor],
        resources=orig_resources,
    )


def build_airflow_polling_sensor(
    airflow_instance: AirflowInstance,
    peered_dag_assets_defs: Dict[str, AssetsDefinition],
    peered_task_specs: Dict[str, Dict[str, AssetSpec]],
    upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
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
        for dag_id, dag_spec in peered_dag_assets_defs.items():
            task_specs = peered_task_specs.get(dag_id, {})
            topo_order_keys = [
                *toposort_task_keys(
                    {val.key for val in task_specs.values()}, upstreams_asset_dependency_graph
                ),
                dag_spec.key,
            ]

            # For now, we materialize assets representing tasks only when the whole dag completes.
            # With a more robust cursor that can let us know when we've seen a particular task run already, then we can relax this constraint.
            for dag_run in airflow_instance.get_dag_runs(dag_id, last_effective_date, current_date):
                # If the dag run succeeded, add materializations for all assets referring to dags.
                if dag_run["state"] != "success":
                    raise Exception("Should not have seen a non-successful dag run.")
                materializations_to_report.extend(
                    [
                        AssetMaterialization(
                            asset_key=task_asset_key,
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
                                    f"[View Run]({airflow_instance.get_dag_run_url(dag_id, dag_run['dag_run_id'])})"
                                ),
                                "Creation Timestamp": TimestampMetadataValue(
                                    get_current_timestamp()
                                ),
                            },
                        )
                        for task_asset_key in topo_order_keys
                    ]
                )
        context.update_cursor(str(current_date.timestamp()))
        return SensorResult(
            asset_events=materializations_to_report,
        )

    return airflow_dag_sensor


def peer_dags(
    airflow_instance: AirflowInstance,
    leaf_keys_per_dag_id: Dict[str, List[AssetKey]],
) -> Dict[str, AssetsDefinition]:
    dag_id_to_asset_spec: Dict[str, AssetsDefinition] = {}
    for dag_info in airflow_instance.list_dags():
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

        spec = AssetSpec(
            key=airflow_instance.get_dag_run_asset_key(dag_info.dag_id),
            description=f"A materialization corresponds to a successful run of airflow DAG {dag_info.dag_id}.",
            metadata=metadata,
            tags={"dagster/compute_kind": "airflow"},
            group_name=f"{airflow_instance.normalized_name}__dags",
            deps=[AssetDep(asset=key) for key in leaf_keys_per_dag_id[dag_info.dag_id]],
        )

        @multi_asset(
            specs=[spec],
            compute_kind="airflow",
            name=f"{dag_info.dag_id}__dag_asset",
            group_name=f"{airflow_instance.normalized_name}__dags",
        )
        def _dag_asset():
            raise NotImplementedError("This is a placeholder function that should never be called.")

        dag_id_to_asset_spec[dag_info.dag_id] = _dag_asset
    return dag_id_to_asset_spec


# We expect that every asset which is passed to this function has all relevant specs mapped to a task.
def get_task_info_for_asset(
    airflow_instance: AirflowInstance, asset: Union[AssetsDefinition, AssetSpec]
) -> TaskInfo:
    # For an AssetSpec, the key must be provided by the tag "airlift/task_id"
    if isinstance(asset, AssetSpec):
        check.invariant(
            "airlift/task_id" in asset.tags,
            "Expected 'airlift/task_id' tag to be present in asset tags.",
        )
        task_id = asset.tags["airlift/task_id"]
    # For an AssetsDefinition, the task_id must be provided by the tag "airlift/task_id" in the op_tags, or the node name.
    elif isinstance(asset, AssetsDefinition):
        if "airlift/task_id" in asset.node_def.tags:
            task_id = asset.node_def.tags["airlift/task_id"]
        else:
            task_id = asset.node_def.name
    check.invariant(
        len(task_id.split("__")) == 2,
        f"Expected task_id to be in the format 'dag_id__task_id'. Instead, got {task_id}",
    )
    dag_id, task_id = task_id.split("__")
    return airflow_instance.get_task_info(dag_id, task_id)


def get_leaf_assets_for_dag(
    asset_keys_in_dag: Set[AssetKey],
    downstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]],
) -> List[AssetKey]:
    # An asset is a "leaf" for the dag if it has no dependencies _within_ the dag. It may have
    # dependencies _outside_ the dag.
    return [
        asset_key
        for asset_key in asset_keys_in_dag
        if downstreams_asset_dependency_graph.get(asset_key, set()).intersection(asset_keys_in_dag)
        == set()
    ]


def toposort_task_keys(
    task_asset_keys: Set[AssetKey], upstreams_asset_dependency_graph: Dict[AssetKey, Set[AssetKey]]
) -> Sequence[AssetKey]:
    narrowed_asset_dependency_graph = {
        key: {dep for dep in deps if dep in task_asset_keys}
        for key, deps in upstreams_asset_dependency_graph.items()
    }
    return toposort_flatten(narrowed_asset_dependency_graph)
