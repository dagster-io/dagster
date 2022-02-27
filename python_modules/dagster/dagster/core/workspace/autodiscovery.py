import inspect
from collections import namedtuple
from typing import NamedTuple

from dagster import (
    DagsterInvariantViolationError,
    GraphDefinition,
    JobDefinition,
    PartitionSetDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
    SensorDefinition,
    check,
)
from dagster.core.asset_defs import AssetGroup
from dagster.core.code_pointer import load_python_file, load_python_module

LoadableTarget = namedtuple("LoadableTarget", "attribute target_definition")


class EphemeralRepositoryTarget(NamedTuple("EphemeralRepositoryTarget", [])):
    pass


def loadable_targets_from_python_file(python_file, working_directory=None):
    loaded_module = load_python_file(python_file, working_directory)
    return _loadable_targets_from_loaded_module(loaded_module)


def loadable_targets_from_python_module(module_name, working_directory, remove_from_path_fn=None):
    module = load_python_module(
        module_name,
        working_directory=working_directory,
        remove_from_path_fn=remove_from_path_fn,
    )
    return _loadable_targets_from_loaded_module(module)


def loadable_targets_from_python_package(package_name, working_directory, remove_from_path_fn=None):
    module = load_python_module(
        package_name, working_directory, remove_from_path_fn=remove_from_path_fn
    )
    return _loadable_targets_from_loaded_module(module)


def _loadable_targets_from_loaded_module(module):
    loadable_repos = _loadable_targets_of_type(module, RepositoryDefinition)
    if loadable_repos:
        return loadable_repos

    # Back-compat for ephemeral single-pipeline case
    loadable_pipelines = _loadable_targets_of_type(module, PipelineDefinition)
    if len(loadable_pipelines) == 1:
        return loadable_pipelines

    # Back-compat for ephemeral single-graph case
    loadable_graphs = _loadable_targets_of_type(module, GraphDefinition)
    if len(loadable_graphs) == 1:
        return loadable_graphs

    # Back-compat for ephemeral single-asset-group case
    loadable_asset_groups = _loadable_targets_of_type(module, AssetGroup)
    if len(loadable_asset_groups) == 1:
        return loadable_asset_groups

    loadable_targets = _get_ephemeral_repository_loadable_targets(module)

    if len(loadable_targets) == 0:
        raise DagsterInvariantViolationError(
            'No jobs, pipelines, asset collections, or repositories found in "{}".'.format(
                module.__name__
            )
        )

    return [EphemeralRepositoryTarget()]


def _get_ephemeral_repository_loadable_targets(module):
    return _loadable_targets_of_type(
        module,
        (
            PipelineDefinition,
            JobDefinition,
            PartitionSetDefinition,
            ScheduleDefinition,
            SensorDefinition,
            AssetGroup,
        ),
    )


def _loadable_targets_of_type(module, klass):
    loadable_targets = []
    for name, value in inspect.getmembers(module):
        if isinstance(value, klass):
            loadable_targets.append(LoadableTarget(name, value))

    return loadable_targets


def create_ephemeral_repository(module):
    from dagster.core.definitions.repository_definition import CachingRepositoryData

    # What about caching?????
    targets = _get_ephemeral_repository_loadable_targets(module)
    check.invariant(len(targets) > 0, "must have at least one code artifact in a repository")
    return RepositoryDefinition(
        name="__repository__",
        repository_data=CachingRepositoryData.from_list(
            [target.target_definition for target in targets]
        ),
    )
