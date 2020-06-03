import importlib
import inspect

from dagster import DagsterInvariantViolationError, PipelineDefinition, RepositoryDefinition
from dagster.core.code_pointer import load_python_file


def loadable_target_from_python_file(python_file):
    loaded_module = load_python_file(python_file)
    return loadable_target_from_loaded_module(loaded_module)


def loadable_target_from_python_module(module_name):
    return loadable_target_from_loaded_module(importlib.import_module(module_name))


def loadable_target_from_loaded_module(module):
    repos = _members_of_type(module, RepositoryDefinition)
    if len(repos) > 1:
        raise DagsterInvariantViolationError(
            (
                'More than one repo found in "{module_name}". Found repositories '
                'defined in variables or decorated functions: {repos}.'
            ).format(module_name=module.__name__, repos=repr([r[0] for r in repos]))
        )

    if len(repos) == 1:
        name, _repo = repos[0]
        return name

    pipelines = _members_of_type(module, PipelineDefinition)

    if len(pipelines) > 1:
        raise DagsterInvariantViolationError(
            (
                'No repository and more than one pipeline found in "{module_name}". If you load '
                'a file or module directly it must either have one repository or one '
                'pipeline in scope. Found pipelines defined in variables or decorated '
                'functions: {pipeline_symbols}.'
            ).format(module_name=module.__name__, pipeline_symbols=repr([p[0] for p in pipelines]))
        )

    if len(pipelines) == 1:
        name, _pipeline = pipelines[0]
        return name

    raise DagsterInvariantViolationError(
        'No pipelines or repositories found in "{}".'.format(module.__name__)
    )


def _members_of_type(module, klass):
    members = []
    for name, value in inspect.getmembers(module):
        if isinstance(value, klass):
            members.append((name, value))

    return members
