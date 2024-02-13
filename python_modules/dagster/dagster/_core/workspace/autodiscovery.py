import inspect
from types import ModuleType
from typing import Callable, NamedTuple, Optional, Sequence, Tuple, Type, Union

from dagster import (
    DagsterInvariantViolationError,
    GraphDefinition,
    RepositoryDefinition,
)
from dagster._core.code_pointer import load_python_file, load_python_module
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.load_assets_from_modules import assets_from_modules
from dagster._core.definitions.repository_definition import PendingRepositoryDefinition

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
    from dagster._core.definitions import JobDefinition

    loadable_defs = _loadable_targets_of_type(module, Definitions)

    if loadable_defs:
        if len(loadable_defs) > 1:
            raise DagsterInvariantViolationError(
                "Cannot have more than one Definitions object defined at module scope"
            )

        return loadable_defs

    loadable_repos = _loadable_targets_of_type(
        module, (RepositoryDefinition, PendingRepositoryDefinition)
    )
    if loadable_repos:
        return loadable_repos

    loadable_jobs = _loadable_targets_of_type(module, JobDefinition)
    loadable_jobs = _loadable_targets_of_type(module, JobDefinition)

    if len(loadable_jobs) == 1:
        return loadable_jobs

    elif len(loadable_jobs) > 1:
        target_type = "job" if len(loadable_jobs) > 1 else "pipeline"
        raise DagsterInvariantViolationError(
            (
                'No repository and more than one {target_type} found in "{module_name}". If you'
                " load a file or module directly it must have only one {target_type} in scope."
                " Found {target_type}s defined in variables or decorated functions:"
                " {pipeline_symbols}."
            ).format(
                module_name=module.__name__,
                pipeline_symbols=repr([p.attribute for p in loadable_jobs]),
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

    module_assets, module_source_assets, _ = assets_from_modules([module])
    if len(module_assets) > 0 or len(module_source_assets) > 0:
        return [LoadableTarget(LOAD_ALL_ASSETS, [*module_assets, *module_source_assets])]

    raise DagsterInvariantViolationError(
        "No repositories, jobs, pipelines, graphs, or asset definitions found in "
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
