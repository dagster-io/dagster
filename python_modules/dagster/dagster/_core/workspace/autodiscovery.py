import inspect
from collections.abc import Sequence
from types import ModuleType
from typing import Callable, NamedTuple, Optional, Union

from dagster import DagsterInvariantViolationError, GraphDefinition, RepositoryDefinition
from dagster._core.code_pointer import load_python_file, load_python_module
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_assets_from_modules import (
    load_assets_from_modules,
)

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


def _format_loadable_def(module: ModuleType, loadable_target: LoadableTarget) -> str:
    return f"{module.__name__}.{loadable_target.attribute}"


def loadable_targets_from_loaded_module(module: ModuleType) -> Sequence[LoadableTarget]:
    from dagster._core.definitions import JobDefinition
    from dagster._utils.test.definitions import LazyDefinitions

    loadable_def_loaders = _loadable_targets_of_type(module, LazyDefinitions)

    if loadable_def_loaders:
        if len(loadable_def_loaders) > 1:
            raise DagsterInvariantViolationError(
                "Cannot have more than one function decorated with @lazy_definitions defined in module scope"
            )

        return loadable_def_loaders

    loadable_defs = _loadable_targets_of_type(module, Definitions)

    if loadable_defs:
        if len(loadable_defs) > 1:
            loadable_def_names = ", ".join(
                _format_loadable_def(module, loadable_def) for loadable_def in loadable_defs
            )
            raise DagsterInvariantViolationError(
                "Cannot have more than one Definitions object defined at module scope."
                f" Found Definitions objects: {loadable_def_names}"
            )

        return loadable_defs

    loadable_repos = _loadable_targets_of_type(module, RepositoryDefinition)
    if loadable_repos:
        return loadable_repos

    loadable_jobs = _loadable_targets_of_type(module, JobDefinition)
    loadable_jobs = _loadable_targets_of_type(module, JobDefinition)

    if len(loadable_jobs) == 1:
        return loadable_jobs

    elif len(loadable_jobs) > 1:
        target_type = "job" if len(loadable_jobs) > 1 else "pipeline"
        raise DagsterInvariantViolationError(
            f'No repository and more than one {target_type} found in "{module.__name__}". If you'
            f" load a file or module directly it must have only one {target_type} in scope."
            f" Found {target_type}s defined in variables or decorated functions:"
            f" {[p.attribute for p in loadable_jobs]!r}."
        )

    loadable_graphs = _loadable_targets_of_type(module, GraphDefinition)

    if len(loadable_graphs) == 1:
        return loadable_graphs

    elif len(loadable_graphs) > 1:
        raise DagsterInvariantViolationError(
            f'More than one graph found in "{module.__name__}". '
            "If you load a file or module directly and it has no repositories, jobs, or "
            "pipelines in scope, it must have no more than one graph in scope. "
            f"Found graphs defined in variables or decorated functions: {[g.attribute for g in loadable_graphs]!r}."
        )

    assets = load_assets_from_modules([module])
    if len(assets) > 0:
        return [LoadableTarget(LOAD_ALL_ASSETS, assets)]

    raise DagsterInvariantViolationError(
        "No Definitions, RepositoryDefinition, Job, Pipeline, Graph, or AssetsDefinition found in "
        f'"{module.__name__}".'
    )


def _loadable_targets_of_type(
    module: ModuleType, klass: Union[type, tuple[type, ...]]
) -> Sequence[LoadableTarget]:
    loadable_targets = []
    for name, value in inspect.getmembers(module):
        if isinstance(value, klass):
            loadable_targets.append(LoadableTarget(name, value))

    return loadable_targets


def autodefs_module_target(autoload_defs_module_name: str, working_directory: Optional[str]):
    from dagster.components import load_defs

    module = load_python_module(autoload_defs_module_name, working_directory)
    defs = load_defs(module)
    return LoadableTarget(
        attribute="",
        target_definition=defs,
    )
