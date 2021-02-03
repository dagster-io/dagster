import os
import sys
from collections import namedtuple
from contextlib import contextmanager

import click
from click import UsageError
from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import repository_def_from_target_def
from dagster.core.host_representation import (
    ExternalRepository,
    ExternalRepositoryOrigin,
    GrpcServerRepositoryLocationOrigin,
    RepositoryLocation,
    RepositoryLocationHandle,
)
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster.grpc.utils import get_loadable_targets
from dagster.utils.hosted_user_process import recon_repository_from_origin

from .load import (
    location_origin_from_module_name,
    location_origin_from_package_name,
    location_origin_from_python_file,
    location_origins_from_yaml_paths,
)
from .workspace import Workspace

WORKSPACE_TARGET_WARNING = "Can only use ONE of --workspace/-w, --python-file/-f, --module-name/-m, --grpc-port, --grpc-socket."


def _cli_load_invariant(condition, msg=None):
    msg = (
        msg
        or "Invalid set of CLI arguments for loading repository/pipeline. See --help for details."
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
    "workspace",
    "python_file",
    "working_directory",
    "empty_working_directory",
    "package_name",
    "module_name",
    "attribute",
    "repository_yaml",
    "grpc_host",
    "grpc_port",
    "grpc_socket",
)

WorkspaceFileTarget = namedtuple("WorkspaceFileTarget", "paths")
PythonFileTarget = namedtuple("PythonFileTarget", "python_file attribute working_directory")
ModuleTarget = namedtuple("ModuleTarget", "module_name attribute")
PackageTarget = namedtuple("PackageTarget", "package_name attribute")
GrpcServerTarget = namedtuple("GrpcServerTarget", "host port socket")

#  Utility target for graphql commands that do not require a workspace, e.g. downloading schema
EmptyWorkspaceTarget = namedtuple("EmptyWorkspaceTarget", "")

WorkspaceLoadTarget = (
    WorkspaceFileTarget,
    PythonFileTarget,
    ModuleTarget,
    PackageTarget,
    EmptyWorkspaceTarget,
    GrpcServerTarget,
)


def created_workspace_load_target(kwargs):
    check.dict_param(kwargs, "kwargs")
    if are_all_keys_empty(kwargs, WORKSPACE_CLI_ARGS):
        if kwargs.get("empty_workspace"):
            return EmptyWorkspaceTarget()
        if os.path.exists("workspace.yaml"):
            return WorkspaceFileTarget(paths=["workspace.yaml"])
        raise click.UsageError("No arguments given and workspace.yaml not found.")

    if kwargs.get("workspace"):
        _check_cli_arguments_none(
            kwargs,
            "python_file",
            "working_directory",
            "empty_working_directory",
            "module_name",
            "package_name",
            "attribute",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        return WorkspaceFileTarget(paths=list(kwargs["workspace"]))
    if kwargs.get("python_file"):
        _check_cli_arguments_none(
            kwargs,
            "module_name",
            "package_name",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        working_directory = get_working_directory_from_kwargs(kwargs)
        return PythonFileTarget(
            python_file=kwargs.get("python_file"),
            attribute=kwargs.get("attribute"),
            working_directory=working_directory,
        )
    if kwargs.get("module_name"):
        _check_cli_arguments_none(
            kwargs,
            "package_name",
            "working_directory",
            "empty_working_directory",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        return ModuleTarget(
            module_name=kwargs.get("module_name"),
            attribute=kwargs.get("attribute"),
        )
    if kwargs.get("package_name"):
        _check_cli_arguments_none(
            kwargs,
            "working_directory",
            "empty_working_directory",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        return PackageTarget(
            package_name=kwargs.get("package_name"),
            attribute=kwargs.get("attribute"),
        )
    if kwargs.get("grpc_port"):
        _check_cli_arguments_none(
            kwargs,
            "attribute",
            "working_directory",
            "empty_working_directory",
            "grpc_socket",
        )
        return GrpcServerTarget(
            port=kwargs.get("grpc_port"),
            socket=None,
            host=(kwargs.get("grpc_host") if kwargs.get("grpc_host") else "localhost"),
        )
    elif kwargs.get("grpc_socket"):
        _check_cli_arguments_none(
            kwargs,
            "attribute",
            "working_directory",
            "empty_working_directory",
        )
        return GrpcServerTarget(
            port=None,
            socket=kwargs.get("grpc_socket"),
            host=(kwargs.get("grpc_host") if kwargs.get("grpc_host") else "localhost"),
        )
    else:
        _cli_load_invariant(False)


def location_origins_from_load_target(load_target):
    if isinstance(load_target, WorkspaceFileTarget):
        return location_origins_from_yaml_paths(
            load_target.paths,
        )
    elif isinstance(load_target, PythonFileTarget):
        return [
            location_origin_from_python_file(
                python_file=load_target.python_file,
                attribute=load_target.attribute,
                working_directory=load_target.working_directory,
            )
        ]
    elif isinstance(load_target, ModuleTarget):
        return [
            location_origin_from_module_name(
                load_target.module_name,
                load_target.attribute,
            )
        ]
    elif isinstance(load_target, PackageTarget):
        return [
            location_origin_from_package_name(
                load_target.package_name,
                load_target.attribute,
            )
        ]
    elif isinstance(load_target, GrpcServerTarget):
        return [
            GrpcServerRepositoryLocationOrigin(
                port=load_target.port,
                socket=load_target.socket,
                host=load_target.host,
            )
        ]
    elif isinstance(load_target, EmptyWorkspaceTarget):
        return []
    else:
        check.not_implemented("Unsupported: {}".format(load_target))


def workspace_from_load_target(load_target):
    check.inst_param(load_target, "load_target", WorkspaceLoadTarget)

    return Workspace(location_origins_from_load_target(load_target))


def get_workspace_from_kwargs(kwargs):
    return workspace_from_load_target(created_workspace_load_target(kwargs))


def python_target_click_options():
    return [
        click.option(
            "--empty-working-directory",
            is_flag=True,
            required=False,
            default=False,
            help="Indicates that the working directory should be empty and should not set to the current "
            "directory as a default",
        ),
        click.option(
            "--working-directory",
            "-d",
            help="Specify working directory to use when loading the repository or pipeline. Can only be used along with -f/--python-file",
        ),
        click.option(
            "--python-file",
            "-f",
            # Checks that the path actually exists lower in the stack, where we
            # are better equipped to surface errors
            type=click.Path(exists=False),
            help="Specify python file where repository or pipeline function lives",
        ),
        click.option(
            "--package-name",
            help="Specify installed Python package where repository or pipeline function lives",
        ),
        click.option(
            "--module-name", "-m", help="Specify module where repository or pipeline function lives"
        ),
        click.option(
            "--attribute",
            "-a",
            help=(
                "Attribute that is either a 1) repository or pipeline or "
                "2) a function that returns a repository or pipeline"
            ),
        ),
    ]


def grpc_server_target_click_options():
    return [
        click.option(
            "--grpc-port",
            type=click.INT,
            required=False,
            help=("Port to use to connect to gRPC server"),
        ),
        click.option(
            "--grpc-socket",
            type=click.Path(),
            required=False,
            help=("Named socket to use to connect to gRPC server"),
        ),
        click.option(
            "--grpc-host",
            type=click.STRING,
            required=False,
            help=("Host to use to connect to gRPC server, defaults to localhost"),
        ),
    ]


def workspace_target_click_options():
    return (
        [
            click.option("--empty-workspace", is_flag=True, help="Allow an empty workspace"),
            click.option(
                "--workspace",
                "-w",
                multiple=True,
                type=click.Path(exists=True),
                help=("Path to workspace file. Argument can be provided multiple times."),
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
                "--repository",
                "-r",
                help=("Repository name, necessary if more than one repository is present."),
            )
        ]
        + [pipeline_option()]
    )


def target_with_config_option(command_name):
    return click.option(
        "-c",
        "--config",
        type=click.Path(exists=True),
        multiple=True,
        help=(
            "Specify one or more run config files. These can also be file patterns. "
            "If more than one run config file is captured then those files are merged. "
            "Files listed first take precedence. They will smash the values of subsequent "
            "files at the key-level granularity. If the file is a pattern then you must "
            "enclose it in double quotes"
            "\n\nExample: "
            "dagster pipeline {name} -f hello_world.py -p pandas_hello_world "
            '-c "pandas_hello_world/*.yaml"'
            "\n\nYou can also specify multiple files:"
            "\n\nExample: "
            "dagster pipeline {name} -f hello_world.py -p pandas_hello_world "
            "-c pandas_hello_world/solids.yaml -e pandas_hello_world/env.yaml"
        ).format(name=command_name),
    )


def python_pipeline_config_argument(command_name):
    def wrap(f):
        return target_with_config_option(command_name)(f)

    return wrap


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
            "--repository",
            "-r",
            help=(
                "Repository within the workspace, necessary if more than one repository is present."
            ),
        ),
        click.option(
            "--location",
            "-l",
            help=(
                "RepositoryLocation within the workspace, necessary if more than one location is present."
            ),
        ),
    )


def pipeline_option():
    return click.option(
        "--pipeline",
        "-p",
        help=("Pipeline within the repository, necessary if more than one pipeline is present."),
    )


def pipeline_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(repository_target_argument(f), pipeline_option())


def get_repository_origin_from_kwargs(kwargs):
    provided_repo_name = kwargs.get("repository")

    if not provided_repo_name:
        raise click.UsageError("Must provide --repository to load a repository")

    repository_location_origin = get_repository_location_origin_from_kwargs(kwargs)

    return ExternalRepositoryOrigin(repository_location_origin, provided_repo_name)


def get_pipeline_python_origin_from_kwargs(kwargs):
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    provided_pipeline_name = kwargs.get("pipeline")

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_definition = recon_repo.get_definition()

    pipeline_names = set(repo_definition.pipeline_names)

    if provided_pipeline_name is None and len(pipeline_names) == 1:
        pipeline_name = next(iter(pipeline_names))
    elif provided_pipeline_name is None:
        raise click.UsageError(
            (
                "Must provide --pipeline as there is more than one pipeline "
                "in {repository}. Options are: {pipelines}."
            ).format(repository=repo_definition.name, pipelines=_sorted_quoted(pipeline_names))
        )
    elif not provided_pipeline_name in pipeline_names:
        raise click.UsageError(
            (
                'Pipeline "{provided_pipeline_name}" not found in repository "{repository_name}". '
                "Found {found_names} instead."
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
    python_file = kwargs.get("python_file")
    module_name = kwargs.get("module_name")
    package_name = kwargs.get("package_name")
    working_directory = get_working_directory_from_kwargs(kwargs)
    attribute = kwargs.get("attribute")
    if python_file:
        _check_cli_arguments_none(kwargs, "module_name", "package_name")
        return {
            repository_def_from_target_def(
                loadable_target.target_definition
            ).name: CodePointer.from_python_file(
                python_file, loadable_target.attribute, working_directory
            )
            for loadable_target in get_loadable_targets(
                python_file, module_name, package_name, working_directory, attribute
            )
        }
    elif module_name:
        _check_cli_arguments_none(kwargs, "python_file", "working_directory", "package_name")
        return {
            repository_def_from_target_def(
                loadable_target.target_definition
            ).name: CodePointer.from_module(module_name, loadable_target.attribute)
            for loadable_target in get_loadable_targets(
                python_file, module_name, package_name, working_directory, attribute
            )
        }
    elif package_name:
        _check_cli_arguments_none(kwargs, "module_name", "python_file", "working_directory")
        return {
            repository_def_from_target_def(
                loadable_target.target_definition
            ).name: CodePointer.from_python_package(package_name, loadable_target.attribute)
            for loadable_target in get_loadable_targets(
                python_file, module_name, package_name, working_directory, attribute
            )
        }
    else:
        check.failed("Must specify a Python file or module name")


def get_working_directory_from_kwargs(kwargs):
    if kwargs.get("empty_working_directory"):
        return None
    return kwargs.get("working_directory") if kwargs.get("working_directory") else os.getcwd()


def get_repository_python_origin_from_kwargs(kwargs):
    provided_repo_name = kwargs.get("repository")

    if not (kwargs.get("python_file") or kwargs.get("module_name") or kwargs.get("package_name")):
        raise click.UsageError("Must specify a python file or module name")

    # Short-circuit the case where an attribute and no repository name is passed in,
    # giving us enough information to return an origin without loading any target
    # definitions - we may need to return an origin for a non-existent repository
    # (e.g. to log an origin ID for an error message)
    if kwargs.get("attribute") and not provided_repo_name:
        if kwargs.get("python_file"):
            _check_cli_arguments_none(kwargs, "module_name", "package_name")
            code_pointer = CodePointer.from_python_file(
                kwargs.get("python_file"),
                kwargs.get("attribute"),
                get_working_directory_from_kwargs(kwargs),
            )
        elif kwargs.get("module_name"):
            _check_cli_arguments_none(kwargs, "python_file", "working_directory", "package_name")
            code_pointer = CodePointer.from_module(
                kwargs.get("module_name"),
                kwargs.get("attribute"),
            )
        elif kwargs.get("package_name"):
            _check_cli_arguments_none(kwargs, "python_file", "working_directory", "module_name")
            code_pointer = CodePointer.from_python_package(
                kwargs.get("package_name"),
                kwargs.get("attribute"),
            )
        else:
            check.failed("Must specify a Python file or module name")
        return RepositoryPythonOrigin(executable_path=sys.executable, code_pointer=code_pointer)

    code_pointer_dict = _get_code_pointer_dict_from_kwargs(kwargs)
    if provided_repo_name is None and len(code_pointer_dict) == 1:
        code_pointer = next(iter(code_pointer_dict.values()))
    elif provided_repo_name is None:
        raise click.UsageError(
            (
                "Must provide --repository as there is more than one repository. "
                "Options are: {repos}."
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


@contextmanager
def get_repository_location_from_kwargs(kwargs):
    origin = get_repository_location_origin_from_kwargs(kwargs)
    with RepositoryLocationHandle.create_from_repository_location_origin(origin) as handle:
        yield RepositoryLocation.from_handle(handle)


def get_repository_location_origin_from_kwargs(kwargs):
    all_origins = location_origins_from_load_target(created_workspace_load_target(kwargs))

    origins_by_name = {origin.location_name: origin for origin in all_origins}

    provided_location_name = kwargs.get("location")

    if provided_location_name is None and len(origins_by_name) == 1:
        return next(iter(origins_by_name.values()))

    elif provided_location_name is None:
        raise click.UsageError(
            (
                "Must provide --location as there are more than one locations "
                "available. Options are: {}"
            ).format(_sorted_quoted(origins_by_name.keys()))
        )

    elif not origins_by_name.get(provided_location_name):
        raise click.UsageError(
            (
                'Location "{provided_location_name}" not found in workspace. '
                "Found {found_names} instead."
            ).format(
                provided_location_name=provided_location_name,
                found_names=_sorted_quoted(origins_by_name.keys()),
            )
        )

    else:
        return origins_by_name.get(provided_location_name)


def get_external_repository_from_repo_location(repo_location, provided_repo_name):
    check.inst_param(repo_location, "repo_location", RepositoryLocation)
    check.opt_str_param(provided_repo_name, "provided_repo_name")

    repo_dict = repo_location.get_repositories()
    check.invariant(repo_dict, "There should be at least one repo.")

    # no name provided and there is only one repo. Automatically return
    if provided_repo_name is None and len(repo_dict) == 1:
        return next(iter(repo_dict.values()))

    if provided_repo_name is None:
        raise click.UsageError(
            (
                "Must provide --repository as there is more than one repository "
                "in {location}. Options are: {repos}."
            ).format(location=repo_location.name, repos=_sorted_quoted(repo_dict.keys()))
        )

    if not repo_location.has_repository(provided_repo_name):
        raise click.UsageError(
            (
                'Repository "{provided_repo_name}" not found in location "{location_name}". '
                "Found {found_names} instead."
            ).format(
                provided_repo_name=provided_repo_name,
                location_name=repo_location.name,
                found_names=_sorted_quoted(repo_dict.keys()),
            )
        )

    return repo_location.get_repository(provided_repo_name)


@contextmanager
def get_external_repository_from_kwargs(kwargs):
    with get_repository_location_from_kwargs(kwargs) as repo_location:
        provided_repo_name = kwargs.get("repository")
        yield get_external_repository_from_repo_location(repo_location, provided_repo_name)


def get_external_pipeline_from_external_repo(external_repo, provided_pipeline_name):
    check.inst_param(external_repo, "external_repo", ExternalRepository)
    check.opt_str_param(provided_pipeline_name, "provided_pipeline_name")

    external_pipelines = {ep.name: ep for ep in external_repo.get_all_external_pipelines()}

    check.invariant(external_pipelines)

    if provided_pipeline_name is None and len(external_pipelines) == 1:
        return next(iter(external_pipelines.values()))

    if provided_pipeline_name is None:
        raise click.UsageError(
            (
                "Must provide --pipeline as there is more than one pipeline "
                "in {repository}. Options are: {pipelines}."
            ).format(
                repository=external_repo.name, pipelines=_sorted_quoted(external_pipelines.keys())
            )
        )

    if not provided_pipeline_name in external_pipelines:
        raise click.UsageError(
            (
                'Pipeline "{provided_pipeline_name}" not found in repository "{repository_name}". '
                "Found {found_names} instead."
            ).format(
                provided_pipeline_name=provided_pipeline_name,
                repository_name=external_repo.name,
                found_names=_sorted_quoted(external_pipelines.keys()),
            )
        )

    return external_pipelines[provided_pipeline_name]


@contextmanager
def get_external_pipeline_from_kwargs(kwargs):
    with get_external_repository_from_kwargs(kwargs) as external_repo:
        provided_pipeline_name = kwargs.get("pipeline")
        yield get_external_pipeline_from_external_repo(external_repo, provided_pipeline_name)


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"
