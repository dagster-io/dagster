import importlib
import inspect
from collections import namedtuple

from dagster import DagsterInvariantViolationError, PipelineDefinition, RepositoryDefinition
from dagster.core.code_pointer import load_python_file

LoadableTarget = namedtuple('LoadableTarget', 'attribute target_definition')


def loadable_targets_from_python_file(python_file):
    loaded_module = load_python_file(python_file)
    return loadable_targets_from_loaded_module(loaded_module)


def loadable_targets_from_python_module(module_name):
    return loadable_targets_from_loaded_module(importlib.import_module(module_name))


def loadable_targets_from_loaded_module(module):
    loadable_repos = _loadable_targets_of_type(module, RepositoryDefinition)
    if loadable_repos:
        return loadable_repos

    loadable_pipelines = _loadable_targets_of_type(module, PipelineDefinition)

    if not loadable_pipelines:
        raise DagsterInvariantViolationError(
            'No pipelines or repositories found in "{}".'.format(module.__name__)
        )

    elif len(loadable_pipelines) > 1:
        raise DagsterInvariantViolationError(
            (
                'No repository and more than one pipeline found in "{module_name}". If you load '
                'a file or module directly it must either have one repository or one '
                'pipeline in scope. Found pipelines defined in variables or decorated '
                'functions: {pipeline_symbols}.'
            ).format(
                module_name=module.__name__,
                pipeline_symbols=repr([p.attribute for p in loadable_pipelines]),
            )
        )

    else:
        return loadable_pipelines


def _loadable_targets_of_type(module, klass):
    loadable_targets = []
    for name, value in inspect.getmembers(module):
        if isinstance(value, klass):
            loadable_targets.append(LoadableTarget(name, value))

    return loadable_targets
