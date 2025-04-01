import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from inspect import isfunction
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

import dagster._check as check
from dagster._config.pythonic_config import (
    ConfigurableIOManagerFactoryResourceDefinition,
    ConfigurableResourceFactoryResourceDefinition,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_job import (
    IMPLICIT_ASSET_JOB_NAME,
    get_base_asset_job_lambda,
    is_reserved_asset_job_name,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition,
    PartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.repository_definition.repository_data import CachingRepositoryData
from dagster._core.definitions.repository_definition.valid_definitions import (
    VALID_REPOSITORY_DATA_DICT_KEYS,
    RepositoryElementDefinition,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.definitions.utils import get_default_automation_condition_sensor
from dagster._core.errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from dagster._core.definitions.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.events import AssetKey

# We throw an error if the user attaches an instance of a custom `PartitionsDefinition` subclass to
# a definition-- we can't support custom PartitionsDefinition subclasses due to us needing to load
# them in the host process.
VALID_PARTITIONS_DEFINITION_CLASSES = (
    StaticPartitionsDefinition,
    DynamicPartitionsDefinition,
    TimeWindowPartitionsDefinition,
    MultiPartitionsDefinition,
)


def _find_env_vars(config_entry: Any) -> set[str]:
    """Given a part of a config dictionary, return a set of environment variables that are used in
    that part of the config.
    """
    # Actual env var entry
    if isinstance(config_entry, Mapping) and set(config_entry.keys()) == {"env"}:
        return {config_entry["env"]}
    # Recurse into dictionary of config items
    elif isinstance(config_entry, Mapping):
        return set().union(*[_find_env_vars(v) for v in config_entry.values()])
    # Recurse into list of config items
    elif isinstance(config_entry, list):
        return set().union(*[_find_env_vars(v) for v in config_entry])

    # Otherwise, raw config value which is not an env var, so return empty set
    return set()


def _env_vars_from_resource_defaults(resource_def: ResourceDefinition) -> set[str]:
    """Given a resource definition, return a set of environment variables that are used in the
    resource's default config. This is used to extract environment variables from the top-level
    resources in a Definitions object.
    """
    from dagster._core.execution.build_resources import wrap_resource_for_execution

    config_schema_default = cast(
        Mapping[str, Any],
        (
            json.loads(resource_def.config_schema.default_value_as_json_str)
            if resource_def.config_schema.default_provided
            else {}
        ),
    )

    env_vars = _find_env_vars(config_schema_default)

    if isinstance(
        resource_def,
        (
            ConfigurableIOManagerFactoryResourceDefinition,
            ConfigurableResourceFactoryResourceDefinition,
        ),
    ):
        nested_resources = resource_def.nested_resources
        for nested_resource in nested_resources.values():
            env_vars = env_vars.union(
                _env_vars_from_resource_defaults(wrap_resource_for_execution(nested_resource))
            )

    return env_vars


def _resolve_unresolved_job_def_lambda(
    unresolved_job_def: UnresolvedAssetJobDefinition,
    asset_graph: AssetGraph,
    default_executor_def: Optional[ExecutorDefinition],
    top_level_resources: Optional[Mapping[str, ResourceDefinition]],
    default_logger_defs: Optional[Mapping[str, LoggerDefinition]],
) -> Callable[[], JobDefinition]:
    def resolve_unresolved_job_def() -> JobDefinition:
        job_def = unresolved_job_def.resolve(
            asset_graph=asset_graph,
            default_executor_def=default_executor_def,
            resource_defs=top_level_resources,
        )
        return _process_resolved_job(job_def, default_executor_def, default_logger_defs)

    return resolve_unresolved_job_def


def _process_resolved_job(
    job_def: JobDefinition,
    default_executor_def: Optional[ExecutorDefinition],
    default_logger_defs: Optional[Mapping[str, LoggerDefinition]],
) -> JobDefinition:
    job_def.validate_resource_requirements_satisfied()

    if default_executor_def and not job_def.has_specified_executor:
        job_def = job_def.with_executor_def(default_executor_def)

    if default_logger_defs and not job_def.has_specified_loggers:
        job_def = job_def.with_logger_defs(default_logger_defs)

    return job_def


def build_caching_repository_data_from_list(
    repository_definitions: Sequence[RepositoryElementDefinition],
    default_executor_def: Optional[ExecutorDefinition] = None,
    default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
    top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
    resource_key_mapping: Optional[Mapping[int, str]] = None,
) -> CachingRepositoryData:
    from dagster._core.definitions import AssetsDefinition
    from dagster._core.definitions.partitioned_schedule import (
        UnresolvedPartitionedAssetScheduleDefinition,
    )

    schedule_and_sensor_names: set[str] = set()
    jobs: dict[str, Union[JobDefinition, Callable[[], JobDefinition]]] = {}
    coerced_graphs: dict[str, JobDefinition] = {}
    unresolved_jobs: dict[str, UnresolvedAssetJobDefinition] = {}
    schedules: dict[str, ScheduleDefinition] = {}
    unresolved_partitioned_asset_schedules: dict[
        str, UnresolvedPartitionedAssetScheduleDefinition
    ] = {}
    sensors: dict[str, SensorDefinition] = {}
    assets_defs: list[AssetsDefinition] = []
    asset_keys: set[AssetKey] = set()
    asset_check_keys: set[AssetCheckKey] = set()
    source_assets: list[SourceAsset] = []
    asset_checks_defs: list[AssetsDefinition] = []
    partitions_defs: set[PartitionsDefinition] = set()
    for definition in repository_definitions:
        if isinstance(definition, JobDefinition):
            if (
                definition.name in jobs and jobs[definition.name] != definition
            ) or definition.name in unresolved_jobs:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate job definition found for {definition.describe_target()}"
                )
            if is_reserved_asset_job_name(definition.name):
                raise DagsterInvalidDefinitionError(
                    f"Attempted to provide job called {definition.name} to repository, which "
                    "is a reserved name. Please rename the job."
                )
            if definition.partitions_def is not None:
                partitions_defs.add(definition.partitions_def)
            jobs[definition.name] = definition
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

        elif isinstance(definition, UnresolvedPartitionedAssetScheduleDefinition):
            if definition.name in schedule_and_sensor_names:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate definition found for {definition.name}"
                )
            schedule_and_sensor_names.add(definition.name)

            unresolved_partitioned_asset_schedules[definition.name] = definition
        elif isinstance(definition, GraphDefinition):
            coerced = definition.coerce_to_job()
            if coerced.name in jobs:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate job definition found for graph '{coerced.name}'"
                )
            jobs[coerced.name] = coerced
            coerced_graphs[coerced.name] = coerced
        elif isinstance(definition, UnresolvedAssetJobDefinition):
            if definition.name in jobs or definition.name in unresolved_jobs:
                raise DagsterInvalidDefinitionError(
                    f"Duplicate definition found for unresolved job '{definition.name}'"
                )
            # we can only resolve these once we have all assets
            if definition.partitions_def is not None:
                partitions_defs.add(definition.partitions_def)
            unresolved_jobs[definition.name] = definition
        elif (
            isinstance(definition, AssetsDefinition)
            and definition.has_check_keys
            and not definition.has_keys
        ):
            for key in definition.check_keys:
                if key in asset_check_keys:
                    raise DagsterInvalidDefinitionError(f"Duplicate asset check key: {key}")
            asset_check_keys.update(definition.check_keys)
            asset_checks_defs.append(definition)
        elif isinstance(definition, AssetsDefinition):
            for spec in definition.specs:
                if spec.key in asset_keys:
                    raise DagsterInvalidDefinitionError(f"Duplicate asset key: {spec.key}")

                if spec.partitions_def is not None:
                    partitions_defs.add(spec.partitions_def)
            for key in definition.check_keys:
                if key in asset_check_keys:
                    raise DagsterInvalidDefinitionError(f"Duplicate asset check key: {key}")

            asset_keys.update(definition.keys)
            asset_check_keys.update(definition.check_keys)
            assets_defs.append(definition)
        elif isinstance(definition, SourceAsset):
            source_assets.append(definition)
            asset_keys.add(definition.key)
        else:
            check.failed(f"Unexpected repository entry {definition}")

    for partitions_def in partitions_defs:
        _validate_partitions_definition(partitions_def)

    source_assets_by_key = {source_asset.key: source_asset for source_asset in source_assets}
    assets_defs_by_key = {key: asset for asset in assets_defs for key in asset.keys}
    asset_checks_defs_by_key = {
        key: checks_def for checks_def in asset_checks_defs for key in checks_def.check_keys
    }

    for name, sensor_def in sensors.items():
        for target in sensor_def.targets:
            if target.has_job_def:
                _process_and_validate_target_job(sensor_def, unresolved_jobs, jobs, target.job_def)
            if target.assets_defs:
                _process_and_validate_target_assets(
                    sensor_def, assets_defs_by_key, source_assets_by_key, target.assets_defs
                )

    for name, schedule_def in schedules.items():
        if schedule_def.target.has_job_def:
            _process_and_validate_target_job(
                schedule_def, unresolved_jobs, jobs, schedule_def.target.job_def
            )
        if schedule_def.target.assets_defs:
            _process_and_validate_target_assets(
                schedule_def,
                assets_defs_by_key,
                source_assets_by_key,
                schedule_def.target.assets_defs,
            )

    if unresolved_partitioned_asset_schedules:
        for (
            name,
            unresolved_partitioned_asset_schedule,
        ) in unresolved_partitioned_asset_schedules.items():
            _process_and_validate_target_job(
                unresolved_partitioned_asset_schedule,
                unresolved_jobs,
                jobs,
                unresolved_partitioned_asset_schedule.job,
            )

    assets_without_keys = [ad for ad in assets_defs if not ad.keys]
    asset_graph = AssetGraph.from_assets(
        [
            # Ensure that the same AssetsDefinition doesn't need to be considered twice by the graph if
            # it produces multiple asset keys
            *set(assets_defs_by_key.values()),
            *assets_without_keys,
            *asset_checks_defs,
            *source_assets_by_key.values(),  # only ever one key per source asset so no need to dedupe
        ]
    )
    # add a default automation condition sensor if necessary
    default_automation_condition_sensor = get_default_automation_condition_sensor(
        list(sensors.values()), asset_graph
    )
    if default_automation_condition_sensor:
        sensors[default_automation_condition_sensor.name] = default_automation_condition_sensor

    if assets_defs or asset_checks_defs or source_assets:
        jobs[IMPLICIT_ASSET_JOB_NAME] = get_base_asset_job_lambda(
            asset_graph=asset_graph,
            executor_def=default_executor_def,
            resource_defs=top_level_resources,
            logger_defs=default_logger_defs,
        )

    _validate_auto_materialize_sensors(sensors.values(), asset_graph)

    # resolve all the UnresolvedAssetJobDefinitions using the full set of assets
    # resolving jobs is potentially time-consuming if there are many of them,
    # so do the resolving lazily in a lambda
    if unresolved_jobs:
        for name, unresolved_job_def in unresolved_jobs.items():
            jobs[name] = _resolve_unresolved_job_def_lambda(
                unresolved_job_def,
                asset_graph,
                default_executor_def,
                top_level_resources,
                default_logger_defs,
            )

    jobs = {
        name: (
            job_def
            if isfunction(job_def)
            else _process_resolved_job(
                cast(JobDefinition, job_def), default_executor_def, default_logger_defs
            )
        )
        for name, job_def in jobs.items()
    }

    top_level_resources = top_level_resources or {}

    utilized_env_vars: dict[str, set[str]] = defaultdict(set)

    for resource_key, resource_def in top_level_resources.items():
        used_env_vars = _env_vars_from_resource_defaults(resource_def)
        for env_var in used_env_vars:
            utilized_env_vars[env_var].add(resource_key)

    return CachingRepositoryData(
        jobs=jobs,
        schedules=schedules,
        sensors=sensors,
        source_assets_by_key=source_assets_by_key,
        assets_defs_by_key=assets_defs_by_key,
        asset_checks_defs_by_key=asset_checks_defs_by_key,
        top_level_resources=top_level_resources or {},
        utilized_env_vars=utilized_env_vars,
        unresolved_partitioned_asset_schedules=unresolved_partitioned_asset_schedules,
    )


def build_caching_repository_data_from_dict(
    repository_definitions: dict[str, dict[str, Any]],
) -> "CachingRepositoryData":
    check.dict_param(repository_definitions, "repository_definitions", key_type=str)
    check.invariant(
        set(repository_definitions.keys()).issubset(VALID_REPOSITORY_DATA_DICT_KEYS),
        "Bad dict: must not contain keys other than {{{valid_keys}}}: found {bad_keys}.".format(
            valid_keys=", ".join([f"'{key}'" for key in VALID_REPOSITORY_DATA_DICT_KEYS]),
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

    for key, raw_job_def in repository_definitions["jobs"].items():
        if isinstance(raw_job_def, GraphDefinition):
            repository_definitions["jobs"][key] = raw_job_def.coerce_to_job()
        elif isinstance(raw_job_def, UnresolvedAssetJobDefinition):
            repository_definitions["jobs"][key] = raw_job_def.resolve(
                # TODO: https://github.com/dagster-io/dagster/issues/8263
                asset_graph=AssetGraph.from_assets([]),
                default_executor_def=None,
            )
        elif not isinstance(raw_job_def, JobDefinition) and not isfunction(raw_job_def):
            raise DagsterInvalidDefinitionError(
                f"Object mapped to {key} is not an instance of JobDefinition or GraphDefinition."
            )

    # Late validate all jobs' resource requirements are satisfied, since
    # they may not be applied until now
    for job_def in repository_definitions["jobs"].values():
        if isinstance(job_def, JobDefinition):
            job_def.validate_resource_requirements_satisfied()

    return CachingRepositoryData(
        **repository_definitions,
        source_assets_by_key={},
        assets_defs_by_key={},
        asset_checks_defs_by_key={},
        top_level_resources={},
        utilized_env_vars={},
        unresolved_partitioned_asset_schedules={},
    )


def _process_and_validate_target_job(
    instigator_def: Union[
        SensorDefinition, ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition
    ],
    unresolved_jobs: dict[str, UnresolvedAssetJobDefinition],
    jobs: dict[str, Union[JobDefinition, Callable[[], JobDefinition]]],
    job_def: Union[JobDefinition, UnresolvedAssetJobDefinition],
):
    """This function modifies the state of unresolved_jobs, and jobs."""
    targeter = (
        f"schedule '{instigator_def.name}'"
        if isinstance(instigator_def, ScheduleDefinition)
        else f"sensor '{instigator_def.name}'"
    )
    if isinstance(job_def, UnresolvedAssetJobDefinition):
        if job_def.name not in unresolved_jobs:
            # Since this is an unresolved job we have to resolve, it is not possible to
            # be the same definition by reference equality
            if job_def.name in jobs:
                raise DagsterInvalidDefinitionError(
                    _get_error_msg_for_target_conflict(
                        targeter, "unresolved asset job", job_def.name, "job"
                    )
                )
        elif unresolved_jobs[job_def.name].selection != job_def.selection:
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(
                    targeter, "unresolved asset job", job_def.name, "unresolved asset job"
                )
            )
        unresolved_jobs[job_def.name] = job_def
    else:
        if job_def.name in jobs and jobs[job_def.name].graph != job_def.graph:  # pyright: ignore[reportFunctionMemberAccess]
            dupe_target_type = "unresolved asset job" if job_def.name in unresolved_jobs else "job"
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(targeter, "job", job_def.name, dupe_target_type)
            )
        jobs[job_def.name] = job_def


def _process_and_validate_target_assets(
    instigator_def: Union[
        SensorDefinition, ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition
    ],
    assets_defs_by_key: dict["AssetKey", AssetsDefinition],
    source_assets_by_key: dict["AssetKey", SourceAsset],
    target_assets_defs: Sequence[Union[AssetsDefinition, SourceAsset]],
) -> None:
    for ad in target_assets_defs:
        keys = ad.keys if isinstance(ad, AssetsDefinition) else [ad.key]
        for key in keys:
            if isinstance(ad, AssetsDefinition):
                existing_ad = assets_defs_by_key.get(key)
                if not existing_ad:
                    assets_defs_by_key[key] = ad
                elif not existing_ad.computation == ad.computation:
                    raise DagsterInvalidDefinitionError(
                        _get_error_msg_for_target_asset_conflict(
                            _get_instigator_str(instigator_def), key.to_user_string()
                        )
                    )
            elif isinstance(ad, SourceAsset):
                existing_sa = source_assets_by_key.get(key)
                if not existing_sa:
                    source_assets_by_key[key] = ad
                elif not ad == existing_sa:
                    raise DagsterInvalidDefinitionError(
                        _get_error_msg_for_target_asset_conflict(
                            _get_instigator_str(instigator_def), key.to_user_string()
                        )
                    )
            else:
                check.failed(f"Unexpected asset definition {ad}")


def _validate_auto_materialize_sensors(
    sensors: Iterable[SensorDefinition], asset_graph: BaseAssetGraph
) -> None:
    """Raises an error if two or more automation policy sensors target the same asset."""
    sensor_names_by_asset_key: dict[AssetKey, str] = {}
    for sensor in sensors:
        if isinstance(sensor, AutomationConditionSensorDefinition):
            asset_keys = sensor.asset_selection.resolve(asset_graph)
            for asset_key in asset_keys:
                if asset_key in sensor_names_by_asset_key:
                    raise DagsterInvalidDefinitionError(
                        f"Automation policy sensors '{sensor.name}' and "
                        f"'{sensor_names_by_asset_key[asset_key]}' have overlapping asset "
                        f"selections: they both target '{asset_key.to_user_string()}'. Each asset "
                        "must only be targeted by one automation policy sensor."
                    )
                else:
                    sensor_names_by_asset_key[asset_key] = sensor.name


def _validate_partitions_definition(partitions_def: PartitionsDefinition) -> None:
    if not isinstance(partitions_def, VALID_PARTITIONS_DEFINITION_CLASSES):
        valid_names = ", ".join([cls.__name__ for cls in VALID_PARTITIONS_DEFINITION_CLASSES])
        raise DagsterInvalidDefinitionError(
            "Custom PartitionsDefinition subclasses are not supported. All passed-in PartitionsDefinition"
            f" objects must be an instance of one of ({valid_names})."
            f" Found instance of {type(partitions_def).__name__}",
        )


def _get_instigator_str(
    instigator_def: Union[
        SensorDefinition, ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition
    ],
) -> str:
    return (
        f"schedule '{instigator_def.name}'"
        if isinstance(
            instigator_def,
            (ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition),
        )
        else f"sensor '{instigator_def.name}'"
    )


def _get_error_msg_for_target_conflict(
    instigator: str, target_type: str, target_name: str, dupe_target_type: str
) -> str:
    return (
        f"{instigator} targets {target_type} '{target_name}', but a different {dupe_target_type} with"
        " the same name was provided. Disambiguate between these by providing a separate name to"
        " one of them."
    )


def _get_error_msg_for_target_asset_conflict(instigator: str, target_name: str) -> str:
    return (
        f"{instigator} targets asset '{target_name}', but a different asset with"
        " the same key was provided. Assets must have unique keys."
    )
