import os
import warnings
from collections import namedtuple

import click
from click import UsageError

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation import RepositoryLocation

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


WORKSPACE_CLI_ARGS = ('workspace', 'python_file', 'module_name', 'attribute', 'repository_yaml')


WorkspaceFileTarget = namedtuple('WorkspaceFileTarget', 'path')
PythonFileTarget = namedtuple('PythonFileTarget', 'python_file attribute')
ModuleTarget = namedtuple('ModuleTarget', 'module_name attribute')

WorkspaceLoadTarget = (WorkspaceFileTarget, PythonFileTarget, ModuleTarget)


def created_workspace_load_target(kwargs):
    check.dict_param(kwargs, 'kwargs')
    if are_all_keys_empty(kwargs, WORKSPACE_CLI_ARGS):
        if os.path.exists('workspace.yaml'):
            return WorkspaceFileTarget(path='workspace.yaml')
        elif os.path.exists('repository.yaml'):
            warnings.warn(
                'You are automatically loading a "repository.yaml", a deprecated '
                'capability. This capability will be eliminated in 0.9.0.'
            )
            return WorkspaceFileTarget(path='repository.yaml')
        raise click.UsageError('No arguments given and workspace.yaml not found.')
    if kwargs.get('repository_yaml'):
        warnings.warn(
            'You have used -y or --repository-yaml to load a workspace. '
            'This is deprecated and will be eliminated in 0.9.0.'
        )
        _check_cli_arguments_none(kwargs, 'python_file', 'module_name', 'attribute', 'workspace')
        return WorkspaceFileTarget(path=kwargs['repository_yaml'])
    if kwargs.get('workspace'):
        _check_cli_arguments_none(kwargs, 'python_file', 'module_name', 'attribute')
        return WorkspaceFileTarget(path=kwargs['workspace'])
    if kwargs.get('python_file'):
        _check_cli_arguments_none(kwargs, 'workspace', 'module_name')
        return PythonFileTarget(
            python_file=kwargs.get('python_file'), attribute=kwargs.get('attribute')
        )
    if kwargs.get('module_name'):
        return ModuleTarget(
            module_name=kwargs.get('module_name'), attribute=kwargs.get('attribute')
        )
    check.failed('invalid')


def workspace_from_load_target(load_target):
    check.inst_param(load_target, 'load_target', WorkspaceLoadTarget)

    if isinstance(load_target, WorkspaceFileTarget):
        return load_workspace_from_yaml_path(load_target.path)
    elif isinstance(load_target, PythonFileTarget):
        return Workspace(
            [location_handle_from_python_file(load_target.python_file, load_target.attribute)]
        )
    elif isinstance(load_target, ModuleTarget):
        return Workspace(
            [location_handle_from_module_name(load_target.module_name, load_target.attribute)]
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


def attribute_option():
    return click.option(
        '--attribute',
        '-a',
        help=(
            'Attribute that is either a 1) repository or pipeline or '
            '2) a function that returns a repository.'
        ),
    )


def workspace_target_click_options():
    return (
        [
            click.option(
                '--workspace', '-w', type=click.Path(exists=True), help=('Path to workspace file')
            ),
            click.option(
                '--repository-yaml',
                '-y',
                type=click.Path(exists=True),
                help=('Path to legacy repository.yaml file'),
            ),
        ]
        + python_target_click_options()
        + [attribute_option()]
    )


def workspace_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *workspace_target_click_options())


def python_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *python_target_click_options())


def origin_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    options = python_target_click_options() + [attribute_option()]
    return apply_click_params(f, *options)


def repository_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(
        workspace_target_argument(f),
        click.option(
            '--repository',
            '-r',
            help=(
                'Repository within the workspace, necessary if more than one repository is present.'
            ),
        ),
        click.option(
            '--location',
            '-l',
            help=(
                'RepositoryLocation within the workspace, necessary if more than one location is present.'
            ),
        ),
    )


def pipeline_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(
        repository_target_argument(f),
        click.option(
            '--pipeline',
            '-p',
            help=(
                'Pipeline within the repository, necessary if more than one pipeline is present.'
            ),
        ),
    )


def get_reconstructable_repository_from_origin_kwargs(kwargs):
    if kwargs.get('python_file'):
        _check_cli_arguments_none(kwargs, 'module_name')
        return ReconstructableRepository.for_file(
            kwargs.get('python_file'), kwargs.get('attribute')
        )
    if kwargs.get('module_name'):
        return ReconstructableRepository.for_module(
            kwargs.get('module_name'), kwargs.get('attribute')
        )
    check.failed('invalid')


def get_repository_location_from_kwargs(kwargs):
    workspace = get_workspace_from_kwargs(kwargs)
    provided_location_name = kwargs.get('location')

    if provided_location_name is None and len(workspace.repository_location_handles) == 1:
        return RepositoryLocation.from_handle(next(iter(workspace.repository_location_handles)))

    if provided_location_name is None:
        raise click.UsageError(
            (
                'Must provide --location as there are more than one locations '
                'available. Options are: {}'
            ).format(_sorted_quoted(workspace.repository_location_names))
        )

    if not workspace.has_repository_location_handle(provided_location_name):
        raise click.UsageError(
            (
                'Location "{provided_location_name}" not found in workspace. '
                'Found {found_names} instead.'
            ).format(
                provided_location_name=provided_location_name,
                found_names=_sorted_quoted(workspace.repository_location_names),
            )
        )

    return RepositoryLocation.from_handle(
        workspace.get_repository_location_handle(provided_location_name)
    )


def get_external_repository_from_kwargs(kwargs):
    repo_location = get_repository_location_from_kwargs(kwargs)

    repo_dict = repo_location.get_repositories()

    provided_repo_name = kwargs.get('repository')

    check.invariant(repo_dict, 'There should be at least one repo.')

    # no name provided and there is only one repo. Automatically return
    if provided_repo_name is None and len(repo_dict) == 1:
        return next(iter(repo_dict.values()))

    if provided_repo_name is None:
        raise click.UsageError(
            (
                'Must provide --repository as there are more than one repositories '
                'in {location}. Options are: {repos}.'
            ).format(location=repo_location.name, repos=_sorted_quoted(repo_dict.keys()))
        )

    if not repo_location.has_repository(provided_repo_name):
        raise click.UsageError(
            (
                'Repository "{provided_repo_name}" not found in location "{location_name}". '
                'Found {found_names} instead.'
            ).format(
                provided_repo_name=provided_repo_name,
                location_name=repo_location.name,
                found_names=_sorted_quoted(repo_dict.keys()),
            )
        )

    return repo_location.get_repository(provided_repo_name)


def get_external_pipeline_from_kwargs(kwargs):
    external_repo = get_external_repository_from_kwargs(kwargs)

    provided_pipeline_name = kwargs.get('pipeline')

    external_pipelines = {ep.name: ep for ep in external_repo.get_all_external_pipelines()}

    check.invariant(external_pipelines)

    if provided_pipeline_name is None and len(external_pipelines) == 1:
        return next(iter(external_pipelines.values()))

    if provided_pipeline_name is None:
        raise click.UsageError(
            (
                'Must provide --pipeline as there is more than one pipeline '
                'in {repository}. Options are: {pipelines}.'
            ).format(
                repository=external_repo.name, pipelines=_sorted_quoted(external_pipelines.keys())
            )
        )

    if not provided_pipeline_name in external_pipelines:
        raise click.UsageError(
            (
                'Pipeline "{provided_pipeline_name}" not found in repository "{repository_name}". '
                'Found {found_names} instead.'
            ).format(
                provided_pipeline_name=provided_pipeline_name,
                repository_name=external_repo.name,
                found_names=_sorted_quoted(external_pipelines.keys()),
            )
        )

    return external_pipelines[provided_pipeline_name]


def _sorted_quoted(strings):
    return '[' + ', '.join(["'{}'".format(s) for s in sorted(list(strings))]) + ']'
