import inspect
from types import ModuleType
from typing import Callable, NamedTuple, Optional, Sequence, Tuple, Type, Union

from dagster import (
    DagsterInvariantViolationError,
    GraphDefinition,
    JobDefinition,
    RepositoryDefinition,
)
from dagster._core.code_pointer import load_python_file, load_python_module
from dagster._core.definitions import AssetGroup
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition import PendingRepositoryDefinition
from dagster._legacy import PipelineDefinition

LOAD_ALL_ASSETS = "<<LOAD_ALL_ASSETS>>"


class LoadableTarget(NamedTuple):
    attribute: str
    target_definition: object


def loadable_targets_from_python_file(
    python_file: str, working_directory: Optional[str] = None
) -> Sequence[LoadableTarget]:
    loaded_module = load_python_file(python_file, working_directory)
    return loadable_targets_from_loaded_module(loaded_module)


def loadable_targets_from_python_module(
    module_name: str,
    working_directory: Optional[str],
    remove_from_path_fn: Optional[Callable[[], Sequence[str]]] = None,
) -> Sequence[LoadableTarget]:
    module = load_python_module(
        module_name,
        working_directory=working_directory,
        remove_from_path_fn=remove_from_path_fn,
    )
    return loadable_targets_from_loaded_module(module)


def loadable_targets_from_python_package(
    package_name: str,
    working_directory: Optional[str],
    remove_from_path_fn: Optional[Callable[[], Sequence[str]]] = None,
) -> Sequence[LoadableTarget]:
    module = load_python_module(
        package_name, working_directory, remove_from_path_fn=remove_from_path_fn
    )
    return loadable_targets_from_loaded_module(module)


def loadable_targets_from_loaded_module(module: ModuleType) -> Sequence[LoadableTarget]:
    loadable_defs = _loadable_targets_of_type(module, Definitions)

    if loadable_defs:
        if len(loadable_defs) > 1:
            raise DagsterInvariantViolationError(
                "Cannot have more than one Definitions object defined at module scope"
            )

        # currently this is super strict and requires that it be named defs
        symbol = loadable_defs[0].attribute
        if symbol != "defs":
            raise DagsterInvariantViolationError(
                f"Found Definitions object at {symbol}. This object must be at a top-level variable named 'defs'."
            )

        return loadable_defs

    loadable_repos = _loadable_targets_of_type(
        module, (RepositoryDefinition, PendingRepositoryDefinition)
    )
    if loadable_repos:
        return loadable_repos

    loadable_pipelines = _loadable_targets_of_type(module, PipelineDefinition)
    loadable_jobs = _loadable_targets_of_type(module, JobDefinition)

    if len(loadable_pipelines) == 1:
        return loadable_pipelines

    elif len(loadable_pipelines) > 1:
        target_type = "job" if len(loadable_jobs) > 1 else "pipeline"
        raise DagsterInvariantViolationError(
            (
                'No repository and more than one {target_type} found in "{module_name}". If you load '
                "a file or module directly it must have only one {target_type} "
                "in scope. Found {target_type}s defined in variables or decorated "
                "functions: {pipeline_symbols}."
            ).format(
                module_name=module.__name__,
                pipeline_symbols=repr([p.attribute for p in loadable_pipelines]),
                target_type=target_type,
            )
        )

    loadable_graphs = _loadable_targets_of_type(module, GraphDefinition)

    if len(loadable_graphs) == 1:
        return loadable_graphs

    elif len(loadable_graphs) > 1:
        raise DagsterInvariantViolationError(
            (
                'More than one graph found in "{module_name}". '
                "If you load a file or module directly and it has no repositories, jobs, or "
                "pipelines in scope, it must have no more than one graph in scope. "
                "Found graphs defined in variables or decorated functions: {graph_symbols}."
            ).format(
                module_name=module.__name__,
                graph_symbols=repr([g.attribute for g in loadable_graphs]),
            )
        )

    loadable_asset_groups = _loadable_targets_of_type(module, AssetGroup)
    if len(loadable_asset_groups) == 1:
        return loadable_asset_groups

    elif len(loadable_asset_groups) > 1:
        var_names = repr([a.attribute for a in loadable_asset_groups])
        raise DagsterInvariantViolationError(
            (
                f'More than one asset group found in "{module.__name__}". '
                "If you load a file or module directly and it has no repositories, jobs, "
                "pipeline, or graphs in scope, it must have no more than one asset group in scope. "
                f"Found asset groups defined in variables: {var_names}."
            )
        )

    asset_group_from_module_assets = AssetGroup.from_modules([module])
    if (
        len(asset_group_from_module_assets.assets) > 0
        or len(asset_group_from_module_assets.source_assets) > 0
    ):
        return [LoadableTarget(LOAD_ALL_ASSETS, asset_group_from_module_assets)]

    raise DagsterInvariantViolationError(
        "No repositories, jobs, pipelines, graphs, asset groups, or asset definitions found in "
        f'"{module.__name__}".'
    )


def _loadable_targets_of_type(
    module: ModuleType, klass: Union[Type, Tuple[Type, ...]]
) -> Sequence[LoadableTarget]:
    loadable_targets = []
    for name, value in inspect.getmembers(module):
        if isinstance(value, klass):
            loadable_targets.append(LoadableTarget(name, value))

    return loadable_targets
