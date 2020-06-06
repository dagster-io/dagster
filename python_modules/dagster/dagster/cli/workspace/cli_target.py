from collections import namedtuple

import click
from click import UsageError

from dagster import check

from .load import (
    load_workspace_from_yaml_path,
    location_handle_from_module_name,
    location_handle_from_python_file,
)
from .workspace import Workspace


def _cli_load_invariant(condition, msg=None):
    msg = (
        msg
        or 'Invalid set of CLI arguments for loading repository/pipeline. See --help for details.'
    )
    if not condition:
        raise UsageError(msg)


def _check_cli_arguments_none(kwargs, *keys):
    for key in keys:
        _cli_load_invariant(not kwargs.get(key))


def are_all_keys_empty(kwargs, keys):
    for key in keys:
        if kwargs.get(key):
            return False

    return True


WORKSPACE_CLI_ARGS = ('workspace', 'python_file', 'module_name', 'definition', 'repository_yaml')


WorkspaceFileTarget = namedtuple('WorkspaceFileTarget', 'path')
PythonFileTarget = namedtuple('PythonFileTarget', 'python_file definition')
ModuleTarget = namedtuple('ModuleTarget', 'module_name definition')

WorkspaceLoadTarget = (WorkspaceFileTarget, PythonFileTarget, ModuleTarget)


def created_workspace_load_target(kwargs):
    check.dict_param(kwargs, 'kwargs')
    if are_all_keys_empty(kwargs, WORKSPACE_CLI_ARGS):
        return WorkspaceFileTarget(path='workspace.yaml')
    if kwargs.get('repository_yaml'):
        _check_cli_arguments_none(kwargs, 'python_file', 'module_name', 'definition', 'workspace')
        return WorkspaceFileTarget(path=kwargs['repository_yaml'])
    if kwargs.get('workspace'):
        _check_cli_arguments_none(kwargs, 'python_file', 'module_name', 'definition')
        return WorkspaceFileTarget(path=kwargs['workspace'])
    if kwargs.get('python_file'):
        _check_cli_arguments_none(kwargs, 'workspace', 'module_name')
        return PythonFileTarget(
            python_file=kwargs.get('python_file'), definition=kwargs.get('definition')
        )
    if kwargs.get('module_name'):
        return ModuleTarget(
            module_name=kwargs.get('module_name'), definition=kwargs.get('definition')
        )
    check.failed('invalid')


def workspace_from_load_target(load_target):
    check.inst_param(load_target, 'load_target', WorkspaceLoadTarget)

    if isinstance(load_target, WorkspaceFileTarget):
        return load_workspace_from_yaml_path(load_target.path)
    elif isinstance(load_target, PythonFileTarget):
        return Workspace(
            [location_handle_from_python_file(load_target.python_file, load_target.definition)]
        )
    elif isinstance(load_target, ModuleTarget):
        return Workspace(
            [location_handle_from_module_name(load_target.module_name, load_target.definition)]
        )
    else:
        check.not_implemented('Unsupported: {}'.format(load_target))


def get_workspace_from_kwargs(kwargs):
    return workspace_from_load_target(created_workspace_load_target(kwargs))


def python_target_click_options():
    return [
        click.option(
            '--python-file',
            '-f',
            type=click.Path(exists=True),
            help='Specify python file where repository or pipeline function lives.',
        ),
        click.option(
            '--module-name', '-m', help='Specify module where repository or pipeline function lives'
        ),
    ]


def workspace_target_click_options():
    return (
        [
            click.option(
                '--workspace', '-w', type=click.Path(exists=True), help=('Path to workspace file')
            )
        ]
        + python_target_click_options()
        + [
            click.option(
                '--definition', '-d', help='Function that returns either repository or pipeline'
            ),
        ]
    )


def workspace_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *workspace_target_click_options())


def python_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *python_target_click_options())
