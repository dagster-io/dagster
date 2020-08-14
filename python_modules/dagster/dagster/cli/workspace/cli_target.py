import os
import sys
import warnings
from collections import namedtuple

import click
from click import UsageError

from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import repository_def_from_target_def
from dagster.core.host_representation import ExternalRepository, RepositoryLocation, UserProcessApi
from dagster.core.host_representation.handle import RepositoryLocationHandle
from dagster.core.instance import DagsterInstance
from dagster.core.origin import (
    PipelinePythonOrigin,
    RepositoryGrpcServerOrigin,
    RepositoryPythonOrigin,
)
from dagster.grpc.utils import get_loadable_targets
from dagster.utils.hosted_user_process import recon_repository_from_origin

from .load import (
    load_workspace_from_yaml_paths,
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


WORKSPACE_CLI_ARGS = (
    'workspace',
    'python_file',
    'working_directory',
    'module_name',
    'attribute',
    'repository_yaml',
    'grpc_host',
    'grpc_port',
    'grpc_socket',
)

WorkspaceFileTarget = namedtuple('WorkspaceFileTarget', 'paths')
PythonFileTarget = namedtuple('PythonFileTarget', 'python_file attribute working_directory')
ModuleTarget = namedtuple('ModuleTarget', 'module_name attribute')
GrpcServerTarget = namedtuple('GrpcServerTarget', 'host port socket')

#  Utility target for graphql commands that do not require a workspace, e.g. downloading schema
EmptyWorkspaceTarget = namedtuple('EmptyWorkspaceTarget', '')

WorkspaceLoadTarget = (
    WorkspaceFileTarget,
    PythonFileTarget,
    ModuleTarget,
    EmptyWorkspaceTarget,
    GrpcServerTarget,
)


def created_workspace_load_target(kwargs):
    check.dict_param(kwargs, 'kwargs')
    if are_all_keys_empty(kwargs, WORKSPACE_CLI_ARGS):
        if kwargs.get('empty_workspace'):
            return EmptyWorkspaceTarget()
        if os.path.exists('workspace.yaml'):
            return WorkspaceFileTarget(paths=['workspace.yaml'])
        elif os.path.exists('repository.yaml'):
            warnings.warn(
                'You are automatically loading a "repository.yaml", a deprecated '
                'capability. This capability will be eliminated in 0.9.0.'
            )
            return WorkspaceFileTarget(paths=['repository.yaml'])
        raise click.UsageError('No arguments given and workspace.yaml not found.')
    if kwargs.get('repository_yaml'):
        warnings.warn(
            'You have used -y or --repository-yaml to load a workspace. '
            'This is deprecated and will be eliminated in 0.9.0.'
        )
        _check_cli_arguments_none(
            kwargs,
            'python_file',
            'working_directory',
            'module_name',
            'attribute',
            'workspace',
            'grpc_host',
            'grpc_port',
            'grpc_socket',
        )
        return WorkspaceFileTarget(paths=[kwargs['repository_yaml']])
    if kwargs.get('workspace'):
        _check_cli_arguments_none(
            kwargs,
            'python_file',
            'working_directory',
            'module_name',
            'attribute',
            'grpc_host',
            'grpc_port',
            'grpc_socket',
        )
        return WorkspaceFileTarget(paths=list(kwargs['workspace']))
    if kwargs.get('python_file'):
        _check_cli_arguments_none(
            kwargs, 'workspace', 'module_name', 'grpc_host', 'grpc_port', 'grpc_socket'
        )
        working_directory = (
            kwargs.get('working_directory') if kwargs.get('working_directory') else os.getcwd()
        )
        return PythonFileTarget(
            python_file=kwargs.get('python_file'),
            attribute=kwargs.get('attribute'),
            working_directory=working_directory,
        )
    if kwargs.get('module_name'):
        _check_cli_arguments_none(
            kwargs,
            'workspace',
            'python_file',
            'working_directory',
            'grpc_host',
            'grpc_port',
            'grpc_socket',
        )
        return ModuleTarget(
            module_name=kwargs.get('module_name'), attribute=kwargs.get('attribute'),
        )
    if kwargs.get('grpc_port'):
        _check_cli_arguments_none(kwargs, 'grpc_socket')
        return GrpcServerTarget(
            port=kwargs.get('grpc_port'),
            socket=None,
            host=(kwargs.get('grpc_host') if kwargs.get('grpc_host') else 'localhost'),
        )
    elif kwargs.get('grpc_socket'):
        return GrpcServerTarget(
            port=None,
            socket=kwargs.get('grpc_socket'),
            host=(kwargs.get('grpc_host') if kwargs.get('grpc_host') else 'localhost'),
        )
    check.failed('invalid')


def workspace_from_load_target(load_target, instance):
    check.inst_param(load_target, 'load_target', WorkspaceLoadTarget)
    check.inst_param(instance, 'instance', DagsterInstance)

    opt_in_settings = instance.get_settings('opt_in')
    python_user_process_api = (
        UserProcessApi.GRPC
        if (opt_in_settings and opt_in_settings['local_servers'])
        else UserProcessApi.CLI
    )

    if isinstance(load_target, WorkspaceFileTarget):
        return load_workspace_from_yaml_paths(load_target.paths, python_user_process_api)
    elif isinstance(load_target, PythonFileTarget):
        return Workspace(
            [
                location_handle_from_python_file(
                    python_file=load_target.python_file,
                    attribute=load_target.attribute,
                    working_directory=load_target.working_directory,
                    user_process_api=python_user_process_api,
                )
            ]
        )
    elif isinstance(load_target, ModuleTarget):
        return Workspace(
            [
                location_handle_from_module_name(
                    load_target.module_name,
                    load_target.attribute,
                    user_process_api=python_user_process_api,
                )
            ]
        )
    elif isinstance(load_target, GrpcServerTarget):
        return Workspace(
            [
                RepositoryLocationHandle.create_grpc_server_location(
                    port=load_target.port, socket=load_target.socket, host=load_target.host,
                )
            ]
        )
    elif isinstance(load_target, EmptyWorkspaceTarget):
        return Workspace([])
    else:
        check.not_implemented('Unsupported: {}'.format(load_target))


def get_workspace_from_kwargs(kwargs, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return workspace_from_load_target(created_workspace_load_target(kwargs), instance)


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
        click.option('--working-directory', '-d', help='Specify working directory'),
        click.option(
            '--attribute',
            '-a',
            help=(
                'Attribute that is either a 1) repository or pipeline or '
                '2) a function that returns a repository or pipeline.'
            ),
        ),
    ]


def grpc_server_target_click_options():
    return [
        click.option('--grpc_port', type=click.INT, required=False),
        click.option('--grpc_socket', type=click.Path(), required=False),
        click.option('--grpc_host', type=click.STRING, required=False),
    ]


def workspace_target_click_options():
    return (
        [
            click.option('--empty-workspace', is_flag=True, help='Allow an empty workspace'),
            click.option(
                '--workspace',
                '-w',
                multiple=True,
                type=click.Path(exists=True),
                help=('Path to workspace file. Argument can be provided multiple times.'),
            ),
            click.option(
                '--repository-yaml',
                '-y',
                type=click.Path(exists=True),
                help=('Path to legacy repository.yaml file'),
            ),
        ]
        + python_target_click_options()
        + grpc_server_target_click_options()
    )


def python_pipeline_target_click_options():
    return (
        python_target_click_options()
        + [
            click.option(
                '--repository',
                '-r',
                help=('Repository name, necessary if more than one repository is present.'),
            )
        ]
        + [pipeline_option()]
    )


def python_pipeline_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *python_pipeline_target_click_options())


def workspace_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *workspace_target_click_options())


def grpc_server_origin_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    options = grpc_server_target_click_options()
    return apply_click_params(f, *options)


def python_origin_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    options = python_target_click_options()
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


def pipeline_option():
    return click.option(
        '--pipeline',
        '-p',
        help=('Pipeline within the repository, necessary if more than one pipeline is present.'),
    )


def pipeline_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(repository_target_argument(f), pipeline_option())


def get_repository_origin_from_kwargs(kwargs):
    load_target = created_workspace_load_target(kwargs)

    if isinstance(load_target, GrpcServerTarget):
        return RepositoryGrpcServerOrigin(
            host=load_target.host,
            port=load_target.port,
            socket=load_target.socket,
            repository_name=kwargs['repository'],
        )

    return get_repository_python_origin_from_kwargs(kwargs)


def get_pipeline_python_origin_from_kwargs(kwargs):
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    provided_pipeline_name = kwargs.get('pipeline')

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_definition = recon_repo.get_definition()

    pipeline_names = set(repo_definition.pipeline_names)

    if provided_pipeline_name is None and len(pipeline_names) == 1:
        pipeline_name = next(iter(pipeline_names))
    elif provided_pipeline_name is None:
        raise click.UsageError(
            (
                'Must provide --pipeline as there is more than one pipeline '
                'in {repository}. Options are: {pipelines}.'
            ).format(repository=repo_definition.name, pipelines=_sorted_quoted(pipeline_names))
        )
    elif not provided_pipeline_name in pipeline_names:
        raise click.UsageError(
            (
                'Pipeline "{provided_pipeline_name}" not found in repository "{repository_name}". '
                'Found {found_names} instead.'
            ).format(
                provided_pipeline_name=provided_pipeline_name,
                repository_name=repo_definition.name,
                found_names=_sorted_quoted(pipeline_names),
            )
        )
    else:
        pipeline_name = provided_pipeline_name

    return PipelinePythonOrigin(pipeline_name, repository_origin=repository_origin)


def _get_code_pointer_dict_from_kwargs(kwargs):
    python_file = kwargs.get('python_file')
    module_name = kwargs.get('module_name')
    working_directory = kwargs.get('working_directory')
    attribute = kwargs.get('attribute')
    loadable_targets = get_loadable_targets(python_file, module_name, working_directory, attribute)
    if python_file:
        return {
            repository_def_from_target_def(
                loadable_target.target_definition
            ).name: CodePointer.from_python_file(
                python_file, loadable_target.attribute, working_directory
            )
            for loadable_target in loadable_targets
        }
    elif module_name:
        return {
            repository_def_from_target_def(
                loadable_target.target_definition
            ).name: CodePointer.from_module(module_name, loadable_target.attribute)
            for loadable_target in loadable_targets
        }
    else:
        check.failed('invalid')


def get_repository_python_origin_from_kwargs(kwargs):
    provided_repo_name = kwargs.get('repository')

    # Short-circuit the case where an attribute and no repository name is passed in,
    # giving us enough information to return an origin without loading any target
    # definitions - we may need to return an origin for a non-existent repository
    # (e.g. to log an origin ID for an error message)
    if kwargs.get('attribute') and not provided_repo_name:
        if kwargs.get('python_file'):
            code_pointer = CodePointer.from_python_file(
                kwargs.get('python_file'), kwargs.get('attribute'), kwargs.get('working_directory')
            )
        elif kwargs.get('module_name'):
            code_pointer = CodePointer.from_module(
                kwargs.get('module_name'), kwargs.get('attribute'),
            )
        else:
            check.failed('Must specify a Python file or module name')
        return RepositoryPythonOrigin(executable_path=sys.executable, code_pointer=code_pointer)

    code_pointer_dict = _get_code_pointer_dict_from_kwargs(kwargs)
    if provided_repo_name is None and len(code_pointer_dict) == 1:
        code_pointer = next(iter(code_pointer_dict.values()))
    elif provided_repo_name is None:
        raise click.UsageError(
            (
                'Must provide --repository as there is more than one repository. '
                'Options are: {repos}.'
            ).format(repos=_sorted_quoted(code_pointer_dict.keys()))
        )
    elif not provided_repo_name in code_pointer_dict:
        raise click.UsageError(
            'Repository "{provided_repo_name}" not found. Found {found_names} instead.'.format(
                provided_repo_name=provided_repo_name,
                found_names=_sorted_quoted(code_pointer_dict.keys()),
            )
        )
    else:
        code_pointer = code_pointer_dict[provided_repo_name]

    return RepositoryPythonOrigin(executable_path=sys.executable, code_pointer=code_pointer)


def get_repository_location_from_kwargs(kwargs, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    workspace = get_workspace_from_kwargs(kwargs, instance)
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


def get_external_repository_from_repo_location(repo_location, provided_repo_name):
    check.inst_param(repo_location, 'repo_location', RepositoryLocation)
    check.opt_str_param(provided_repo_name, 'provided_repo_name')

    repo_dict = repo_location.get_repositories()
    check.invariant(repo_dict, 'There should be at least one repo.')

    # no name provided and there is only one repo. Automatically return
    if provided_repo_name is None and len(repo_dict) == 1:
        return next(iter(repo_dict.values()))

    if provided_repo_name is None:
        raise click.UsageError(
            (
                'Must provide --repository as there is more than one repository '
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


def get_external_repository_from_kwargs(kwargs, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    repo_location = get_repository_location_from_kwargs(kwargs, instance)
    provided_repo_name = kwargs.get('repository')
    return get_external_repository_from_repo_location(repo_location, provided_repo_name)


def get_external_pipeline_from_external_repo(external_repo, provided_pipeline_name):
    check.inst_param(external_repo, 'external_repo', ExternalRepository)
    check.opt_str_param(provided_pipeline_name, 'provided_pipeline_name')

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


def get_external_pipeline_from_kwargs(kwargs, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    external_repo = get_external_repository_from_kwargs(kwargs, instance)
    provided_pipeline_name = kwargs.get('pipeline')
    return get_external_pipeline_from_external_repo(external_repo, provided_pipeline_name)


def _sorted_quoted(strings):
    return '[' + ', '.join(["'{}'".format(s) for s in sorted(list(strings))]) + ']'
