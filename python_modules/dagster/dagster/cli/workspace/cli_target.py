import os
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Dict, Generator, Iterable, List, Optional, Tuple, Union, cast

import click
from click import UsageError

import dagster._check as check
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstruct import repository_def_from_target_def
from dagster.core.definitions.repository_definition import RepositoryDefinition
from dagster.core.host_representation.external import ExternalRepository
from dagster.core.host_representation.repository_location import RepositoryLocation
from dagster.core.instance import DagsterInstance
from dagster.core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    PipelinePythonOrigin,
    RepositoryPythonOrigin,
)
from dagster.core.workspace.context import WorkspaceRequestContext
from dagster.core.workspace.load_target import (
    EmptyWorkspaceTarget,
    GrpcServerTarget,
    ModuleTarget,
    PackageTarget,
    PythonFileTarget,
    WorkspaceFileTarget,
)
from dagster.grpc.utils import get_loadable_targets
from dagster.utils.hosted_user_process import recon_repository_from_origin

if TYPE_CHECKING:
    from dagster.core.workspace.context import WorkspaceProcessContext

from dagster.core.host_representation.external import ExternalPipeline

WORKSPACE_TARGET_WARNING = "Can only use ONE of --workspace/-w, --python-file/-f, --module-name/-m, --grpc-port, --grpc-socket."


def _cli_load_invariant(condition: object, msg=None) -> None:
    msg = (
        msg
        or "Invalid set of CLI arguments for loading repository/pipeline. See --help for details."
    )
    if not condition:
        raise UsageError(msg)


def _check_cli_arguments_none(kwargs: Dict[str, str], *keys: str) -> None:
    for key in keys:
        _cli_load_invariant(not kwargs.get(key))


def are_all_keys_empty(kwargs: Dict[str, str], keys: Iterable[str]) -> bool:
    for key in keys:
        if kwargs.get(key):
            return False

    return True


WORKSPACE_CLI_ARGS = (
    "workspace",
    "python_file",
    "working_directory",
    "package_name",
    "module_name",
    "attribute",
    "repository_yaml",
    "grpc_host",
    "grpc_port",
    "grpc_socket",
)


def get_workspace_load_target(kwargs: Dict[str, str]):
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
            "module_name",
            "package_name",
            "attribute",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        return WorkspaceFileTarget(paths=list(cast(Union[List, Tuple], kwargs.get("workspace"))))
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
            python_file=check.str_elem(kwargs, "python_file"),
            attribute=check.opt_str_elem(kwargs, "attribute"),
            working_directory=working_directory,
            location_name=None,
        )
    if kwargs.get("module_name"):
        _check_cli_arguments_none(
            kwargs,
            "package_name",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        working_directory = get_working_directory_from_kwargs(kwargs)
        return ModuleTarget(
            module_name=check.str_elem(kwargs, "module_name"),
            attribute=check.opt_str_elem(kwargs, "attribute"),
            working_directory=working_directory,
            location_name=None,
        )
    if kwargs.get("package_name"):
        _check_cli_arguments_none(
            kwargs,
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )
        working_directory = get_working_directory_from_kwargs(kwargs)
        return PackageTarget(
            package_name=check.str_elem(kwargs, "package_name"),
            attribute=check.opt_str_elem(kwargs, "attribute"),
            working_directory=working_directory,
            location_name=None,
        )
    if kwargs.get("grpc_port"):
        _check_cli_arguments_none(
            kwargs,
            "attribute",
            "working_directory",
            "grpc_socket",
        )
        return GrpcServerTarget(
            port=check.int_elem(kwargs, "grpc_port"),
            socket=None,
            host=check.opt_str_elem(kwargs, "grpc_host") or "localhost",
            location_name=None,
        )
    elif kwargs.get("grpc_socket"):
        _check_cli_arguments_none(
            kwargs,
            "attribute",
            "working_directory",
        )
        return GrpcServerTarget(
            port=None,
            socket=check.str_elem(kwargs, "grpc_socket"),
            host=check.opt_str_elem(kwargs, "grpc_host") or "localhost",
            location_name=None,
        )
    else:
        _cli_load_invariant(False)
        # necessary for pyright, does not understand _cli_load_invariant(False) never returns
        assert False


def get_workspace_process_context_from_kwargs(
    instance: DagsterInstance, version: str, read_only: bool, kwargs: Dict[str, str]
) -> "WorkspaceProcessContext":
    from dagster.core.workspace import WorkspaceProcessContext

    return WorkspaceProcessContext(
        instance, get_workspace_load_target(kwargs), version=version, read_only=read_only
    )


@contextmanager
def get_workspace_from_kwargs(
    instance: DagsterInstance, version: str, kwargs: Dict[str, str]
) -> Generator[WorkspaceRequestContext, None, None]:
    with get_workspace_process_context_from_kwargs(
        instance, version, read_only=False, kwargs=kwargs
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def python_target_click_options(is_using_job_op_graph_apis: bool = False):
    return [
        click.option(
            "--working-directory",
            "-d",
            help=f"Specify working directory to use when loading the repository or {'job' if is_using_job_op_graph_apis else 'pipeline/job'}.",
            envvar="DAGSTER_WORKING_DIRECTORY",
        ),
        click.option(
            "--python-file",
            "-f",
            # Checks that the path actually exists lower in the stack, where we
            # are better equipped to surface errors
            type=click.Path(exists=False),
            help=f"Specify python file where repository or {'job' if is_using_job_op_graph_apis else 'pipeline/job'} function lives",
            envvar="DAGSTER_PYTHON_FILE",
        ),
        click.option(
            "--package-name",
            help=f"Specify Python package where repository or {'job' if is_using_job_op_graph_apis else 'pipeline/job'} function lives",
            envvar="DAGSTER_PACKAGE_NAME",
        ),
        click.option(
            "--module-name",
            "-m",
            help=f"Specify module where repository or {'job' if is_using_job_op_graph_apis else 'pipeline/job'} function lives",
            envvar="DAGSTER_MODULE_NAME",
        ),
        click.option(
            "--attribute",
            "-a",
            help=(
                f"Attribute that is either a 1) repository or {'job' if is_using_job_op_graph_apis else 'pipeline/job'} or "
                f"2) a function that returns a repository or {'job' if is_using_job_op_graph_apis else 'pipeline/job'}"
            ),
            envvar="DAGSTER_ATTRIBUTE",
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
        click.option(
            "--use-ssl",
            is_flag=True,
            required=False,
            help=("Use a secure channel when connecting to the gRPC server"),
        ),
    ]


def workspace_target_click_options(using_job_op_graph_apis: bool = False):
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
        + python_target_click_options(using_job_op_graph_apis)
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


def python_job_target_click_options():
    return (
        python_target_click_options(is_using_job_op_graph_apis=True)
        + [
            click.option(
                "--repository",
                "-r",
                help=("Repository name, necessary if more than one repository is present."),
            )
        ]
        + [job_option()]
    )


def target_with_config_option(command_name, using_job_op_graph_apis):
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
            "dagster {pipeline_or_job} {name} -f hello_world.py {pipeline_or_job_flag} pandas_hello_world "
            '-c "pandas_hello_world/*.yaml"'
            "\n\nYou can also specify multiple files:"
            "\n\nExample: "
            "dagster {pipeline_or_job} {name} -f hello_world.py {pipeline_or_job_flag} pandas_hello_world "
            "-c pandas_hello_world/solids.yaml -c pandas_hello_world/env.yaml"
        ).format(
            name=command_name,
            pipeline_or_job="job" if using_job_op_graph_apis else "pipeline",
            pipeline_or_job_flag="-j" if using_job_op_graph_apis else "-p",
        ),
    )


def python_pipeline_or_job_config_argument(command_name, using_job_op_graph_apis=False):
    def wrap(f):
        return target_with_config_option(command_name, using_job_op_graph_apis)(f)

    return wrap


def python_pipeline_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *python_pipeline_target_click_options())


def python_job_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *python_job_target_click_options())


def workspace_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *workspace_target_click_options())


def job_workspace_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(f, *workspace_target_click_options(using_job_op_graph_apis=True))


def grpc_server_origin_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    options = grpc_server_target_click_options()
    return apply_click_params(f, *options)


def python_origin_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    options = python_target_click_options()
    return apply_click_params(f, *options)


def repository_click_options():
    return [
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
    ]


def repository_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(workspace_target_argument(f), *repository_click_options())


def job_repository_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(job_workspace_target_argument(f), *repository_click_options())


def pipeline_option():
    return click.option(
        "--pipeline",
        "-p",
        "pipeline_or_job",
        help=(
            "Pipeline/Job within the repository, necessary if more than one pipeline/job is present."
        ),
    )


def pipeline_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(repository_target_argument(f), pipeline_option())


def job_option():
    return click.option(
        "--job",
        "-j",
        "pipeline_or_job",
        help=("Job within the repository, necessary if more than one job is present."),
    )


def job_target_argument(f):
    from dagster.cli.pipeline import apply_click_params

    return apply_click_params(job_repository_target_argument(f), job_option())


def get_pipeline_or_job_python_origin_from_kwargs(kwargs, using_job_op_graph_apis=False):
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    provided_pipeline_name = kwargs.get("pipeline_or_job")

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_definition = recon_repo.get_definition()

    pipeline_or_job_names = set(
        repo_definition.job_names if using_job_op_graph_apis else repo_definition.pipeline_names
    )

    if provided_pipeline_name is None and len(pipeline_or_job_names) == 1:
        pipeline_name = next(iter(pipeline_or_job_names))
    elif provided_pipeline_name is None:
        raise click.UsageError(
            (
                "Must provide {flag} as there is more than one pipeline/job "
                "in {repository}. Options are: {pipelines}."
            ).format(
                flag="--job" if using_job_op_graph_apis else "--pipeline",
                repository=repo_definition.name,
                pipelines=_sorted_quoted(pipeline_or_job_names),
            )
        )
    elif not provided_pipeline_name in pipeline_or_job_names:
        raise click.UsageError(
            (
                'Pipeline/Job "{provided_pipeline_name}" not found in repository "{repository_name}". '
                "Found {found_names} instead."
            ).format(
                provided_pipeline_name=provided_pipeline_name,
                repository_name=repo_definition.name,
                found_names=_sorted_quoted(pipeline_or_job_names),
            )
        )
    else:
        pipeline_name = provided_pipeline_name

    return PipelinePythonOrigin(pipeline_name, repository_origin=repository_origin)


def _get_code_pointer_dict_from_kwargs(kwargs: Dict[str, str]) -> Dict[str, CodePointer]:
    python_file = kwargs.get("python_file")
    module_name = kwargs.get("module_name")
    package_name = kwargs.get("package_name")
    working_directory = get_working_directory_from_kwargs(kwargs)
    attribute = kwargs.get("attribute")
    if python_file:
        _check_cli_arguments_none(kwargs, "module_name", "package_name")
        return {
            cast(
                RepositoryDefinition,
                repository_def_from_target_def(loadable_target.target_definition),
            ).name: CodePointer.from_python_file(
                python_file, loadable_target.attribute, working_directory
            )
            for loadable_target in get_loadable_targets(
                python_file, module_name, package_name, working_directory, attribute
            )
        }
    elif module_name:
        _check_cli_arguments_none(kwargs, "python_file", "package_name")
        return {
            cast(
                RepositoryDefinition,
                repository_def_from_target_def(loadable_target.target_definition),
            ).name: CodePointer.from_module(
                module_name, loadable_target.attribute, working_directory
            )
            for loadable_target in get_loadable_targets(
                python_file, module_name, package_name, working_directory, attribute
            )
        }
    elif package_name:
        _check_cli_arguments_none(kwargs, "module_name", "python_file")
        return {
            cast(
                RepositoryDefinition,
                repository_def_from_target_def(loadable_target.target_definition),
            ).name: CodePointer.from_python_package(
                package_name, loadable_target.attribute, working_directory
            )
            for loadable_target in get_loadable_targets(
                python_file, module_name, package_name, working_directory, attribute
            )
        }
    else:
        check.failed("Must specify a Python file or module name")


def get_working_directory_from_kwargs(kwargs: Dict[str, str]) -> Optional[str]:
    return check.opt_str_elem(kwargs, "working_directory") or os.getcwd()


def get_repository_python_origin_from_kwargs(kwargs: Dict[str, str]) -> RepositoryPythonOrigin:
    provided_repo_name = cast(str, kwargs.get("repository"))

    if not (kwargs.get("python_file") or kwargs.get("module_name") or kwargs.get("package_name")):
        raise click.UsageError("Must specify a python file or module name")

    # Short-circuit the case where an attribute and no repository name is passed in,
    # giving us enough information to return an origin without loading any target
    # definitions - we may need to return an origin for a non-existent repository
    # (e.g. to log an origin ID for an error message)
    if kwargs.get("attribute") and not provided_repo_name:
        if kwargs.get("python_file"):
            _check_cli_arguments_none(kwargs, "module_name", "package_name")
            code_pointer: CodePointer = CodePointer.from_python_file(
                kwargs["python_file"],
                kwargs["attribute"],
                get_working_directory_from_kwargs(kwargs),
            )
        elif kwargs.get("module_name"):
            _check_cli_arguments_none(kwargs, "python_file", "package_name")
            code_pointer = CodePointer.from_module(
                kwargs["module_name"],
                kwargs["attribute"],
                get_working_directory_from_kwargs(kwargs),
            )
        elif kwargs.get("package_name"):
            _check_cli_arguments_none(kwargs, "python_file", "module_name")
            code_pointer = CodePointer.from_python_package(
                kwargs["package_name"],
                kwargs["attribute"],
                get_working_directory_from_kwargs(kwargs),
            )
        else:
            check.failed("Must specify a Python file or module name")
        return RepositoryPythonOrigin(
            executable_path=sys.executable,
            code_pointer=code_pointer,
            entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
        )

    code_pointer_dict = _get_code_pointer_dict_from_kwargs(kwargs)
    found_repo_names = _sorted_quoted(code_pointer_dict.keys())
    if provided_repo_name is None and len(code_pointer_dict) == 1:
        code_pointer = next(iter(code_pointer_dict.values()))
    elif provided_repo_name is None:
        raise click.UsageError(
            (
                "Must provide --repository as there is more than one repository. "
                f"Options are: {found_repo_names}."
            )
        )
    elif not provided_repo_name in code_pointer_dict:
        raise click.UsageError(
            f'Repository "{provided_repo_name}" not found. Found {found_repo_names} instead.'
        )
    else:
        code_pointer = code_pointer_dict[provided_repo_name]

    return RepositoryPythonOrigin(
        executable_path=sys.executable,
        code_pointer=code_pointer,
        entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
    )


@contextmanager
def get_repository_location_from_kwargs(instance, version, kwargs):
    # Instance isn't strictly required to load a repository location, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_workspace_from_kwargs(instance, version, kwargs) as workspace:
        yield get_repository_location_from_workspace(workspace, kwargs.get("location"))


def get_repository_location_from_workspace(
    workspace: WorkspaceRequestContext, provided_location_name
):
    if provided_location_name is None:
        if len(workspace.repository_location_names) == 1:
            provided_location_name = workspace.repository_location_names[0]
        elif len(workspace.repository_location_names) == 0:
            raise click.UsageError("No locations found in workspace")
        elif provided_location_name is None:
            raise click.UsageError(
                (
                    "Must provide --location as there are multiple locations "
                    "available. Options are: {}"
                ).format(_sorted_quoted(workspace.repository_location_names))
            )

    if provided_location_name not in workspace.repository_location_names:
        raise click.UsageError(
            (
                'Location "{provided_location_name}" not found in workspace. '
                "Found {found_names} instead."
            ).format(
                provided_location_name=provided_location_name,
                found_names=_sorted_quoted(workspace.repository_location_names),
            )
        )

    if workspace.has_repository_location_error(provided_location_name):
        raise click.UsageError(
            'Error loading location "{provided_location_name}": {error_str}'.format(
                provided_location_name=provided_location_name,
                error_str=str(workspace.get_repository_location_error(provided_location_name)),
            )
        )

    return workspace.get_repository_location(provided_location_name)


def get_external_repository_from_repo_location(
    repo_location: RepositoryLocation, provided_repo_name: Optional[str]
) -> ExternalRepository:
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
def get_external_repository_from_kwargs(instance, version, kwargs):
    # Instance isn't strictly required to load an ExternalRepository, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_repository_location_from_kwargs(instance, version, kwargs) as repo_location:
        provided_repo_name = kwargs.get("repository")
        yield get_external_repository_from_repo_location(repo_location, provided_repo_name)


def get_external_pipeline_or_job_from_external_repo(
    external_repo: ExternalRepository,
    provided_pipeline_or_job_name: Optional[str],
    using_job_op_graph_apis: bool = False,
) -> ExternalPipeline:
    check.inst_param(external_repo, "external_repo", ExternalRepository)
    check.opt_str_param(provided_pipeline_or_job_name, "provided_pipeline_or_job_name")

    external_pipelines = {
        ep.name: ep
        for ep in (
            external_repo.get_external_jobs()
            if using_job_op_graph_apis
            else external_repo.get_all_external_pipelines()
        )
    }

    check.invariant(external_pipelines)

    if provided_pipeline_or_job_name is None and len(external_pipelines) == 1:
        return next(iter(external_pipelines.values()))

    if provided_pipeline_or_job_name is None:
        raise click.UsageError(
            (
                "Must provide {flag} as there is more than one pipeline/job "
                "in {repository}. Options are: {pipelines}."
            ).format(
                flag="--job" if using_job_op_graph_apis else "--pipeline",
                repository=external_repo.name,
                pipelines=_sorted_quoted(external_pipelines.keys()),
            )
        )

    if not provided_pipeline_or_job_name in external_pipelines:
        raise click.UsageError(
            (
                '{pipeline_or_job} "{provided_pipeline_name}" not found in repository "{repository_name}". '
                "Found {found_names} instead."
            ).format(
                pipeline_or_job="Job" if using_job_op_graph_apis else "Pipeline",
                provided_pipeline_name=provided_pipeline_or_job_name,
                repository_name=external_repo.name,
                found_names=_sorted_quoted(external_pipelines.keys()),
            )
        )

    return external_pipelines[provided_pipeline_or_job_name]


@contextmanager
def get_external_pipeline_or_job_from_kwargs(
    instance, version, kwargs, using_job_op_graph_apis=False
):
    # Instance isn't strictly required to load an ExternalPipeline, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_external_repository_from_kwargs(instance, version, kwargs) as external_repo:
        provided_pipeline_or_job_name = kwargs.get("pipeline_or_job")
        yield get_external_pipeline_or_job_from_external_repo(
            external_repo, provided_pipeline_or_job_name, using_job_op_graph_apis
        )


def _sorted_quoted(strings):
    return "[" + ", ".join(["'{}'".format(s) for s in sorted(list(strings))]) + "]"
