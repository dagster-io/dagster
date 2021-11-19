import inspect
from collections import namedtuple

from dagster import (
    DagsterInvariantViolationError,
    GraphDefinition,
    JobDefinition,
    PipelineDefinition,
    RepositoryDefinition,
)
from dagster.core.code_pointer import load_python_file, load_python_module

LoadableTarget = namedtuple("LoadableTarget", "attribute target_definition")


def loadable_targets_from_python_file(python_file, working_directory=None):
    loaded_module = load_python_file(python_file, working_directory)
    return loadable_targets_from_loaded_module(loaded_module)


def loadable_targets_from_python_module(module_name, remove_from_path_fn=None):
    module = load_python_module(
        module_name, warn_only=True, remove_from_path_fn=remove_from_path_fn
    )
    return loadable_targets_from_loaded_module(module)


def loadable_targets_from_python_package(package_name, remove_from_path_fn=None):
    module = load_python_module(package_name, remove_from_path_fn=remove_from_path_fn)
    return loadable_targets_from_loaded_module(module)


def loadable_targets_from_loaded_module(module):
    loadable_repos = _loadable_targets_of_type(module, RepositoryDefinition)
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
                'No repository, job, or pipeline, and more than one graph found in "{module_name}". '
                "If you load a file or module directly it must either have one repository, one "
                "job, one pipeline, or one graph in scope. Found graphs defined in variables or "
                "decorated functions: {graph_symbols}."
            ).format(
                module_name=module.__name__,
                graph_symbols=repr([g.attribute for g in loadable_graphs]),
            )
        )

    else:
        raise DagsterInvariantViolationError(
            'No jobs, pipelines, graphs, or repositories found in "{}".'.format(module.__name__)
        )


def _loadable_targets_of_type(module, klass):
    loadable_targets = []
    for name, value in inspect.getmembers(module):
        if isinstance(value, klass):
            loadable_targets.append(LoadableTarget(name, value))

    return loadable_targets
