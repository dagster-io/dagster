from inspect import isfunction
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
)

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.assets_job import (
    get_base_asset_jobs,
    is_base_asset_job_name,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.partition import PartitionSetDefinition
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvalidDefinitionError

from .repository_data import CachingRepositoryData, _get_partition_set_from_schedule
from .valid_definitions import VALID_REPOSITORY_DATA_DICT_KEYS, RepositoryListDefinition


def build_caching_repository_data_from_list(
    repository_definitions: Sequence[RepositoryListDefinition],
    default_executor_def: Optional[ExecutorDefinition] = None,
    default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
    top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
) -> CachingRepositoryData:
    from dagster._core.definitions import AssetGroup, AssetsDefinition
    from dagster._core.definitions.partitioned_schedule import (
        UnresolvedPartitionedAssetScheduleDefinition,
    )

    schedule_and_sensor_names: Set[str] = set()
    pipelines_or_jobs: Dict[str, Union[PipelineDefinition, JobDefinition]] = {}
    coerced_graphs: Dict[str, JobDefinition] = {}
    unresolved_jobs: Dict[str, UnresolvedAssetJobDefinition] = {}
    partition_sets: Dict[str, PartitionSetDefinition[object]] = {}
    schedules: Dict[str, ScheduleDefinition] = {}
    unresolved_partitioned_asset_schedules: Dict[
        str, UnresolvedPartitionedAssetScheduleDefinition
    ] = {}
    sensors: Dict[str, SensorDefinition] = {}
    assets_defs: List[AssetsDefinition] = []
    asset_keys: Set[AssetKey] = set()
    source_assets: List[SourceAsset] = []
    combined_asset_group = None
    for definition in repository_definitions:
        if isinstance(definition, PipelineDefinition):
            if (
                definition.name in pipelines_or_jobs
                and pipelines_or_jobs[definition.name] != definition
            ) or definition.name in unresolved_jobs:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate {definition.target_type} definition found for"
                    f" {definition.describe_target()}"
                )
            if is_base_asset_job_name(definition.name):
                raise DagsterInvalidDefinitionError(
                    f"Attempted to provide job called {definition.name} to repository, which "
                    "is a reserved name. Please rename the job."
                )
            pipelines_or_jobs[definition.name] = definition
        elif isinstance(definition, PartitionSetDefinition):
            if definition.name in partition_sets:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate partition set definition found for partition set {definition.name}"
                )
            partition_sets[definition.name] = definition
        elif isinstance(definition, SensorDefinition):
            if definition.name in schedule_and_sensor_names:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate definition found for {definition.name}"
                )
            schedule_and_sensor_names.add(definition.name)
            sensors[definition.name] = definition
        elif isinstance(definition, ScheduleDefinition):
            if definition.name in schedule_and_sensor_names:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate definition found for {definition.name}"
                )
            schedule_and_sensor_names.add(definition.name)

            schedules[definition.name] = definition
            partition_set_def = _get_partition_set_from_schedule(definition)
            if partition_set_def:
                if (
                    partition_set_def.name in partition_sets
                    and partition_set_def != partition_sets[partition_set_def.name]
                ):
                    raise DagsterInvalidDefinitionError(
                        "Duplicate partition set definition found for partition set "
                        f"{partition_set_def.name}"
                    )
                partition_sets[partition_set_def.name] = partition_set_def

        elif isinstance(definition, UnresolvedPartitionedAssetScheduleDefinition):
            if definition.name in schedule_and_sensor_names:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate definition found for {definition.name}"
                )
            schedule_and_sensor_names.add(definition.name)

            unresolved_partitioned_asset_schedules[definition.name] = definition
        elif isinstance(definition, GraphDefinition):
            coerced = definition.coerce_to_job()
            if coerced.name in pipelines_or_jobs:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate {coerced.target_type} definition found for graph '{coerced.name}'"
                )
            pipelines_or_jobs[coerced.name] = coerced
            coerced_graphs[coerced.name] = coerced
        elif isinstance(definition, UnresolvedAssetJobDefinition):
            if definition.name in pipelines_or_jobs or definition.name in unresolved_jobs:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate definition found for unresolved job '{definition.name}'"
                )
            # we can only resolve these once we have all assets
            unresolved_jobs[definition.name] = definition
        elif isinstance(definition, AssetGroup):
            if combined_asset_group:
                combined_asset_group += definition
            else:
                combined_asset_group = definition
        elif isinstance(definition, AssetsDefinition):
            for key in definition.keys:
                if key in asset_keys:
                    raise DagsterInvalidDefinitionError(f"Duplicate asset key: {key}")

            asset_keys.update(definition.keys)
            assets_defs.append(definition)
        elif isinstance(definition, SourceAsset):
            source_assets.append(definition)
        else:
            check.failed(f"Unexpected repository entry {definition}")

    if assets_defs or source_assets:
        if combined_asset_group is not None:
            raise DagsterInvalidDefinitionError(
                "A repository can't have both an AssetGroup and direct asset defs"
            )
        combined_asset_group = AssetGroup(
            assets=assets_defs,
            source_assets=source_assets,
            executor_def=default_executor_def,
        )

    if combined_asset_group:
        for job_def in get_base_asset_jobs(
            assets=combined_asset_group.assets,
            source_assets=combined_asset_group.source_assets,
            executor_def=combined_asset_group.executor_def,
            resource_defs=combined_asset_group.resource_defs,
        ):
            pipelines_or_jobs[job_def.name] = job_def

        source_assets_by_key = {
            source_asset.key: source_asset for source_asset in combined_asset_group.source_assets
        }
        assets_defs_by_key = {
            key: asset for asset in combined_asset_group.assets for key in asset.keys
        }
    else:
        source_assets_by_key = {}
        assets_defs_by_key = {}

    asset_graph = AssetGraph.from_assets(
        [*combined_asset_group.assets, *combined_asset_group.source_assets]
        if combined_asset_group
        else []
    )

    # resolve all the UnresolvedAssetJobDefinitions and
    # UnresolvedPartitionedAssetScheduleDefinitions using the full set of assets
    if unresolved_partitioned_asset_schedules:
        for (
            name,
            unresolved_partitioned_asset_schedule,
        ) in unresolved_partitioned_asset_schedules.items():
            schedules[name] = unresolved_partitioned_asset_schedule.resolve(asset_graph)
            if schedules[name].has_loadable_target():
                target = schedules[name].load_target()
                _process_and_validate_target(
                    schedules[name], coerced_graphs, unresolved_jobs, pipelines_or_jobs, target
                )

    for name, sensor_def in sensors.items():
        if sensor_def.has_loadable_targets():
            targets = sensor_def.load_targets()
            for target in targets:
                _process_and_validate_target(
                    sensor_def, coerced_graphs, unresolved_jobs, pipelines_or_jobs, target
                )

    for name, schedule_def in schedules.items():
        if schedule_def.has_loadable_target():
            target = schedule_def.load_target()
            _process_and_validate_target(
                schedule_def, coerced_graphs, unresolved_jobs, pipelines_or_jobs, target
            )

    if unresolved_jobs:
        for name, unresolved_job_def in unresolved_jobs.items():
            resolved_job = unresolved_job_def.resolve(
                asset_graph=asset_graph, default_executor_def=default_executor_def
            )
            pipelines_or_jobs[name] = resolved_job

    pipelines: Dict[str, PipelineDefinition] = {}
    jobs: Dict[str, JobDefinition] = {}
    for name, pipeline_or_job in pipelines_or_jobs.items():
        if isinstance(pipeline_or_job, JobDefinition):
            jobs[name] = pipeline_or_job
        else:
            pipelines[name] = pipeline_or_job

    if default_executor_def:
        for name, job_def in jobs.items():
            if not job_def._executor_def_specified:  # pylint: disable=protected-access
                jobs[name] = job_def.with_executor_def(default_executor_def)

    if default_logger_defs:
        for name, job_def in jobs.items():
            if not job_def._logger_defs_specified:  # pylint: disable=protected-access
                jobs[name] = job_def.with_logger_defs(default_logger_defs)

    return CachingRepositoryData(
        pipelines=pipelines,
        jobs=jobs,
        partition_sets=partition_sets,
        schedules=schedules,
        sensors=sensors,
        source_assets_by_key=source_assets_by_key,
        assets_defs_by_key=assets_defs_by_key,
        top_level_resources=top_level_resources or {},
    )


def build_caching_repository_data_from_dict(
    repository_definitions: Dict[str, Dict[str, Any]]
) -> "CachingRepositoryData":
    check.dict_param(repository_definitions, "repository_definitions", key_type=str)
    check.invariant(
        set(repository_definitions.keys()).issubset(VALID_REPOSITORY_DATA_DICT_KEYS),
        "Bad dict: must not contain keys other than {{{valid_keys}}}: found {bad_keys}.".format(
            valid_keys=", ".join(
                ["'{key}'".format(key=key) for key in VALID_REPOSITORY_DATA_DICT_KEYS]
            ),
            bad_keys=", ".join(
                [
                    "'{key}'"
                    for key in repository_definitions.keys()
                    if key not in VALID_REPOSITORY_DATA_DICT_KEYS
                ]
            ),
        ),
    )

    for key in VALID_REPOSITORY_DATA_DICT_KEYS:
        if key not in repository_definitions:
            repository_definitions[key] = {}

    duplicate_keys = set(repository_definitions["schedules"].keys()).intersection(
        set(repository_definitions["sensors"].keys())
    )
    if duplicate_keys:
        raise DagsterInvalidDefinitionError(
            "Duplicate definitions between schedules and sensors found for keys:"
            f" {', '.join(duplicate_keys)}"
        )

    # merge jobs in to pipelines while they are just implemented as pipelines
    for key, job in repository_definitions["jobs"].items():
        if key in repository_definitions["pipelines"]:
            raise DagsterInvalidDefinitionError(
                f'Conflicting entries for name {key} in "jobs" and "pipelines".'
            )

        if isinstance(job, GraphDefinition):
            repository_definitions["jobs"][key] = job.coerce_to_job()
        elif isinstance(job, UnresolvedAssetJobDefinition):
            repository_definitions["jobs"][key] = job.resolve(
                # TODO: https://github.com/dagster-io/dagster/issues/8263
                assets=[],
                source_assets=[],
                default_executor_def=None,
            )
        elif not isinstance(job, JobDefinition) and not isfunction(job):
            raise DagsterInvalidDefinitionError(
                f"Object mapped to {key} is not an instance of JobDefinition or GraphDefinition."
            )

    return CachingRepositoryData(
        **repository_definitions,
        source_assets_by_key={},
        assets_defs_by_key={},
        top_level_resources={},
    )


def _process_and_validate_target(
    schedule_or_sensor_def: Union[SensorDefinition, ScheduleDefinition],
    coerced_graphs: Dict[str, JobDefinition],
    unresolved_jobs: Dict[str, UnresolvedAssetJobDefinition],
    pipelines_or_jobs: Dict[str, PipelineDefinition],
    target: Union[GraphDefinition, PipelineDefinition, UnresolvedAssetJobDefinition],
):
    """
    This function modifies the state of coerced_graphs, unresolved_jobs, and pipelines_or_jobs
    """
    targeter = (
        f"schedule '{schedule_or_sensor_def.name}'"
        if isinstance(schedule_or_sensor_def, ScheduleDefinition)
        else f"sensor '{schedule_or_sensor_def.name}'"
    )
    if isinstance(target, GraphDefinition):
        if target.name not in coerced_graphs:
            # Since this is a graph we have to coerce, it is not possible to be
            # the same definition by reference equality
            if target.name in pipelines_or_jobs:
                dupe_target_type = pipelines_or_jobs[target.name].target_type
                raise DagsterInvalidDefinitionError(
                    _get_error_msg_for_target_conflict(
                        targeter, "graph", target.name, dupe_target_type
                    )
                )
        elif coerced_graphs[target.name].graph != target:
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(targeter, "graph", target.name, "graph")
            )
        coerced_job = target.coerce_to_job()
        coerced_graphs[target.name] = coerced_job
        pipelines_or_jobs[target.name] = coerced_job
    elif isinstance(target, UnresolvedAssetJobDefinition):
        if target.name not in unresolved_jobs:
            # Since this is an unresolved job we have to resolve, it is not possible to
            # be the same definition by reference equality
            if target.name in pipelines_or_jobs:
                dupe_target_type = pipelines_or_jobs[target.name].target_type
                raise DagsterInvalidDefinitionError(
                    _get_error_msg_for_target_conflict(
                        targeter, "unresolved asset job", target.name, dupe_target_type
                    )
                )
        elif unresolved_jobs[target.name].selection != target.selection:
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(
                    targeter, "unresolved asset job", target.name, "unresolved asset job"
                )
            )
        unresolved_jobs[target.name] = target
    else:
        if target.name in pipelines_or_jobs and pipelines_or_jobs[target.name] != target:
            dupe_target_type = (
                "graph"
                if target.name in coerced_graphs
                else "unresolved asset job"
                if target.name in unresolved_jobs
                else pipelines_or_jobs[target.name].target_type
            )
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(
                    targeter, target.target_type, target.name, dupe_target_type
                )
            )
        pipelines_or_jobs[target.name] = target


def _get_error_msg_for_target_conflict(targeter, target_type, target_name, dupe_target_type):
    return (
        f"{targeter} targets {target_type} '{target_name}', but a different {dupe_target_type} with"
        " the same name was provided. Disambiguate between these by providing a separate name to"
        " one of them."
    )
