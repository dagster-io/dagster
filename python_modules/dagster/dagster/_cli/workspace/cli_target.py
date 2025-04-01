import logging
import os
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar, cast

import click
from click import UsageError
from dagster_shared.seven import JSONDecodeError, json
from dagster_shared.yaml_utils import load_yaml_from_glob_list
from typing_extensions import Never, Self, TypeAlias

import dagster._check as check
from dagster import __version__ as dagster_version
from dagster._cli.utils import has_pyproject_dagster_block, serialize_sorted_quoted
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.reconstruct import repository_def_from_target_def
from dagster._core.instance import DagsterInstance
from dagster._core.origin import DEFAULT_DAGSTER_ENTRY_POINT, RepositoryPythonOrigin
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import RemoteJob, RemoteRepository
from dagster._core.remote_representation.origin import (
    CodeLocationOrigin,
    GrpcServerCodeLocationOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import (
    CompositeTarget,
    EmptyWorkspaceTarget,
    GrpcServerTarget,
    InProcessWorkspaceLoadTarget,
    ModuleTarget,
    PackageTarget,
    PyProjectFileTarget,
    PythonFileTarget,
    WorkspaceFileTarget,
    WorkspaceLoadTarget,
)
from dagster._grpc.utils import get_loadable_targets
from dagster._record import record
from dagster._utils.error import serializable_error_info_from_exc_info

logger = logging.getLogger("dagster")
WORKSPACE_TARGET_WARNING = (
    "Can only use ONE of --workspace/-w, --python-file/-f, --module-name/-m, --grpc-port,"
    " --grpc-socket."
)

T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])


WORKSPACE_CLI_ARGS = (
    "workspace",
    "python_file",
    "working_directory",
    "package_name",
    "module_name",
    "attribute",
    "grpc_host",
    "grpc_port",
    "grpc_socket",
)


def _get_workspace_load_target_from_cli_opts(
    workspace_opts: "WorkspaceOpts",
) -> WorkspaceLoadTarget:
    if _are_attrs_falsey(workspace_opts, *WORKSPACE_CLI_ARGS):
        if workspace_opts.empty_workspace:
            return EmptyWorkspaceTarget()
        elif has_pyproject_dagster_block("pyproject.toml"):
            return PyProjectFileTarget("pyproject.toml")
        elif os.path.exists("workspace.yaml"):
            return WorkspaceFileTarget(paths=["workspace.yaml"])
        else:
            raise click.UsageError(
                "No arguments given and no [tool.dagster] block in pyproject.toml found."
            )

    if workspace_opts.workspace:
        _check_attrs_falsey(
            workspace_opts,
            *(k for k in WORKSPACE_CLI_ARGS if k not in ["workspace"]),
        )
        return WorkspaceFileTarget(paths=list(workspace_opts.workspace))

    elif workspace_opts.python_file:
        _check_attrs_falsey(
            workspace_opts,
            *(
                k
                for k in WORKSPACE_CLI_ARGS
                if k not in ["python_file", "attribute", "working_directory"]
            ),
        )
        working_directory = workspace_opts.working_directory or os.getcwd()

        if len(workspace_opts.python_file) == 1:
            return PythonFileTarget(
                python_file=workspace_opts.python_file[0],
                attribute=workspace_opts.attribute,
                working_directory=working_directory,
                location_name=None,
            )
        else:
            # multiple files

            if workspace_opts.attribute:
                raise UsageError(
                    "If you are specifying multiple files you cannot specify an attribute."
                )

            return CompositeTarget(
                targets=[
                    PythonFileTarget(
                        python_file=python_file,
                        attribute=None,
                        working_directory=working_directory,
                        location_name=None,
                    )
                    for python_file in workspace_opts.python_file
                ]
            )

    elif workspace_opts.module_name:
        _check_attrs_falsey(
            workspace_opts,
            *(
                k
                for k in WORKSPACE_CLI_ARGS
                if k not in ["module_name", "attribute", "working_directory"]
            ),
        )

        working_directory = workspace_opts.working_directory or os.getcwd()

        if len(workspace_opts.module_name) == 1:
            return ModuleTarget(
                module_name=workspace_opts.module_name[0],
                attribute=workspace_opts.attribute,
                working_directory=working_directory,
                location_name=None,
            )
        else:
            # multiple modules

            if workspace_opts.attribute:
                raise UsageError(
                    "If you are specifying multiple modules you cannot specify an attribute. Got"
                    f" modules {workspace_opts.module_name}."
                )

            return CompositeTarget(
                targets=[
                    ModuleTarget(
                        module_name=module_name,
                        attribute=None,
                        working_directory=working_directory,
                        location_name=None,
                    )
                    for module_name in workspace_opts.module_name
                ]
            )

    elif workspace_opts.package_name:
        _check_attrs_falsey(
            workspace_opts,
            *(
                k
                for k in WORKSPACE_CLI_ARGS
                if k not in ["package_name", "attribute", "working_directory"]
            ),
        )
        working_directory = workspace_opts.working_directory or os.getcwd()

        if len(workspace_opts.package_name) == 1:
            return PackageTarget(
                package_name=workspace_opts.package_name[0],
                attribute=workspace_opts.attribute,
                working_directory=working_directory,
                location_name=None,
            )
        else:
            if workspace_opts.attribute:
                raise UsageError(
                    "If you are specifying multiple packages you cannot specify an attribute. Got"
                    f" packages {workspace_opts.package_name}."
                )

            return CompositeTarget(
                targets=[
                    PackageTarget(
                        package_name=package_name,
                        attribute=None,
                        working_directory=working_directory,
                        location_name=None,
                    )
                    for package_name in workspace_opts.package_name
                ]
            )

    elif workspace_opts.grpc_port:
        _check_attrs_falsey(
            workspace_opts,
            *(k for k in WORKSPACE_CLI_ARGS if k not in ["grpc_port", "grpc_host"]),
        )
        return GrpcServerTarget(
            port=workspace_opts.grpc_port,
            socket=None,
            host=workspace_opts.grpc_host or "localhost",
            location_name=None,
        )
    elif workspace_opts.grpc_socket:
        _check_attrs_falsey(
            workspace_opts,
            *(k for k in WORKSPACE_CLI_ARGS if k not in ["grpc_socket", "grpc_host"]),
        )
        return GrpcServerTarget(
            port=None,
            socket=workspace_opts.grpc_socket,
            host=workspace_opts.grpc_host or "localhost",
            location_name=None,
        )
    else:
        _raise_cli_usage_error()


@contextmanager
def get_workspace_from_cli_opts(
    instance: DagsterInstance,
    version: str,
    workspace_opts: "WorkspaceOpts",
    allow_in_process: bool = False,
    log_level: str = "INFO",
) -> Iterator[WorkspaceRequestContext]:
    load_target = workspace_opts.to_load_target(allow_in_process)
    if isinstance(load_target, InProcessWorkspaceLoadTarget):
        logger.debug("Loading workspace in-process")
    else:
        logger.debug("Loading workspace with gRPC server")

    with WorkspaceProcessContext(
        instance=instance,
        version=version,
        read_only=False,
        workspace_load_target=load_target,
        code_server_log_level=log_level,
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


@contextmanager
def get_repository_from_cli_opts(
    instance: DagsterInstance,
    version: str,
    workspace_opts: "WorkspaceOpts",
    repository_opts: Optional["RepositoryOpts"],
) -> Iterator[RemoteRepository]:
    # Instance isn't strictly required to load a RemoteRepository, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_workspace_from_cli_opts(
        instance, version=dagster_version, workspace_opts=workspace_opts
    ) as workspace:
        repository_name = repository_opts.repository if repository_opts else None
        location_name = repository_opts.location if repository_opts else None
        code_location = get_code_location_from_workspace(workspace, location_name)
        yield get_remote_repository_from_code_location(code_location, repository_name)


@contextmanager
def get_job_from_cli_opts(
    instance: DagsterInstance,
    version: str,
    workspace_opts: "WorkspaceOpts",
    repository_opts: Optional["RepositoryOpts"],
    job_name: Optional[str],
) -> Iterator[RemoteJob]:
    # Instance isn't strictly required to load an RemoteJob, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_repository_from_cli_opts(instance, version, workspace_opts, repository_opts) as repo:
        yield get_remote_job_from_remote_repo(repo, job_name)


# ########################
# ##### VALUE OBJECTS
# ########################

# These classes correspond to the reusable option groups defined in the decorators below. When one
# of these decorators is used, the resulting options should be immediately parsed into the
# corresponding value object at the top of the click command body, by calling
# `extract_from_cli_options`.


@record
class PythonPointerOpts:
    python_file: Optional[str] = None
    module_name: Optional[str] = None
    package_name: Optional[str] = None
    working_directory: Optional[str] = None
    attribute: Optional[str] = None

    @classmethod
    def extract_from_cli_options(cls, cli_options: dict[str, Any]) -> Self:
        # This is expected to always be called from a click entry point, so all options should be
        # present in the dictionary. We rely on `@record` for type-checking.
        return cls(
            python_file=cli_options.pop("python_file"),
            module_name=cli_options.pop("module_name"),
            package_name=cli_options.pop("package_name"),
            working_directory=cli_options.pop("working_directory"),
            attribute=cli_options.pop("attribute"),
        )

    def to_workspace_opts(self) -> "WorkspaceOpts":
        return WorkspaceOpts(
            python_file=(self.python_file,) if self.python_file else None,
            module_name=(self.module_name,) if self.module_name else None,
            package_name=(self.package_name,) if self.package_name else None,
            working_directory=self.working_directory,
            attribute=self.attribute,
        )


@record
class WorkspaceOpts:
    empty_workspace: bool = False
    workspace: Optional[Sequence[str]] = None

    # Like PythonPointerParams but multiple files/modules/packages are allowed
    python_file: Optional[Sequence[str]] = None
    module_name: Optional[Sequence[str]] = None
    package_name: Optional[Sequence[str]] = None
    working_directory: Optional[str] = None
    attribute: Optional[str] = None

    # For gRPC server
    grpc_port: Optional[int] = None
    grpc_socket: Optional[str] = None
    grpc_host: Optional[str] = None
    use_ssl: bool = False

    @classmethod
    def extract_from_cli_options(cls, cli_options: dict[str, Any]) -> Self:
        # This is expected to always be called from a click entry point, so all options should be
        # present in the dictionary. We rely on `@record` for type-checking.
        return cls(
            empty_workspace=cli_options.pop("empty_workspace"),
            workspace=cli_options.pop("workspace"),
            python_file=cli_options.pop("python_file"),
            module_name=cli_options.pop("module_name"),
            package_name=cli_options.pop("package_name"),
            working_directory=cli_options.pop("working_directory"),
            attribute=cli_options.pop("attribute"),
            grpc_port=cli_options.pop("grpc_port"),
            grpc_socket=cli_options.pop("grpc_socket"),
            grpc_host=cli_options.pop("grpc_host"),
            use_ssl=cli_options.pop("use_ssl"),
        )

    def to_load_target(self, allow_in_process: bool = False) -> WorkspaceLoadTarget:
        load_target = _get_workspace_load_target_from_cli_opts(self)
        origins = load_target.create_origins()

        # We can load a workspace in-process if there is only one origin and the python executable is
        # unspecified or matches that of the current process.
        origins = load_target.create_origins()
        can_load_in_process = len(origins) == 1 and _origin_executable_matches_current_process(
            origins[0]
        )
        if allow_in_process and can_load_in_process:
            origin = origins[0]
            return InProcessWorkspaceLoadTarget(
                [
                    InProcessCodeLocationOrigin(
                        origin.loadable_target_origin,
                        container_image=None,
                        location_name=origin.location_name,
                    )
                ]
            )
        else:
            return load_target


def _origin_executable_matches_current_process(origin: CodeLocationOrigin) -> bool:
    # loadable_target_origin is unknown for GrpcServerCodeLocationOrigin
    return not isinstance(origin, GrpcServerCodeLocationOrigin) and (
        origin.loadable_target_origin.executable_path is None
        or origin.loadable_target_origin.executable_path == sys.executable
    )


@record
class RepositoryOpts:
    repository: Optional[str] = None
    location: Optional[str] = None

    @classmethod
    def extract_from_cli_options(cls, cli_options: dict[str, object]) -> Self:
        return cls(
            repository=check.opt_inst(cli_options.pop("repository"), str),
            location=check.opt_inst(cli_options.pop("location"), str),
        )


# ########################
# ##### CLICK DECORATORS
# ########################

# These are named as *_options and can be directly applied to click commands/groups as decorators.
# They contain various subsets from the generate_*


def run_config_option(*, name: str, command_name: str) -> Callable[[T_Callable], T_Callable]:
    def wrap(f: T_Callable) -> T_Callable:
        return _apply_click_params(f, _generate_run_config_option(name, command_name))

    return wrap


def job_name_option(f: Optional[T_Callable] = None, *, name: str) -> T_Callable:
    if f is None:
        return lambda f: job_name_option(f, name=name)  # type: ignore
    else:
        return _apply_click_params(f, _generate_job_name_option(name))


def repository_name_option(f: Optional[T_Callable] = None, *, name: str) -> T_Callable:
    if f is None:
        return lambda f: repository_name_option(f, name=name)  # type: ignore
    else:
        return _apply_click_params(f, _generate_repository_name_option(name))


def workspace_options(f: T_Callable) -> T_Callable:
    return _apply_click_params(f, *_generate_workspace_options())


def python_pointer_options(f: T_Callable) -> T_Callable:
    return _apply_click_params(f, *_generate_python_pointer_options(allow_multiple=False))


def repository_options(f: T_Callable) -> T_Callable:
    return _apply_click_params(
        f,
        _generate_repository_name_option("repository"),
        _generate_code_location_name_option("location"),
    )


ClickOption: TypeAlias = Callable[[T_Callable], T_Callable]


def _apply_click_params(command: T_Callable, *click_params: ClickOption) -> T_Callable:
    for click_param in click_params:
        command = click_param(command)
    return command


# ########################
# ##### OPTION GENERATORS
# ########################

# These are named as generate_*_option(s) and return a ClickOption or list of Click Options. These
# cannot be directly applied to click commands/groups as decorators. They are intended to be private
# to this module-- external code should use the below decorators.


def _generate_job_name_option(name: str) -> ClickOption:
    return click.option(
        "--job",
        "-j",
        name,
        help="Job within the repository, necessary if more than one job is present.",
    )


def _generate_repository_name_option(name: str) -> ClickOption:
    return click.option(
        "--repository",
        "-r",
        name,
        help=(
            "Name of the repository, necessary if more than one repository is present in the"
            " code location."
        ),
    )


def _generate_code_location_name_option(name: str) -> ClickOption:
    return click.option(
        "--location",
        "-l",
        name,
        help="Name of the code location, necessary if more than one location is present.",
    )


def _generate_run_config_option(name: str, command_name: str) -> ClickOption:
    return click.option(
        "-c",
        "--config",
        name,
        type=click.Path(exists=True),
        multiple=True,
        help=(
            "Specify one or more run config files. These can also be file patterns. "
            "If more than one run config file is captured then those files are merged. "
            "Files listed first take precedence. They will smash the values of subsequent "
            "files at the key-level granularity. If the file is a pattern then you must "
            "enclose it in double quotes"
            "\n\nExample: "
            f"dagster job {command_name} -f hello_world.py -j pandas_hello_world "
            '-c "pandas_hello_world/*.yaml"'
            "\n\nYou can also specify multiple files:"
            "\n\nExample: "
            f"dagster job {command_name} -f hello_world.py -j pandas_hello_world "
            "-c pandas_hello_world/ops.yaml -c pandas_hello_world/env.yaml"
        ),
    )


def _generate_python_pointer_options(allow_multiple: bool) -> Sequence[ClickOption]:
    return [
        click.option(
            "--working-directory",
            "-d",
            help="Specify working directory to use when loading the repository or job",
            envvar="DAGSTER_WORKING_DIRECTORY",
        ),
        click.option(
            "--python-file",
            "-f",
            # Checks that the path actually exists lower in the stack, where we
            # are better equipped to surface errors
            type=click.Path(exists=False),
            multiple=allow_multiple,
            help=(
                "Specify python file "
                + ("or files (flag can be used multiple times) " if allow_multiple else "")
                + "where dagster definitions reside as top-level symbols/variables and load "
                + ("each" if allow_multiple else "the")
                + " file as a code location in the current python environment."
            ),
            envvar="DAGSTER_PYTHON_FILE",
        ),
        click.option(
            "--module-name",
            "-m",
            multiple=allow_multiple,
            help=(
                "Specify module "
                + ("or modules (flag can be used multiple times) " if allow_multiple else "")
                + "where dagster definitions reside as top-level symbols/variables and load "
                + ("each" if allow_multiple else "the")
                + " module as a code location in the current python environment."
            ),
            envvar="DAGSTER_MODULE_NAME",
        ),
        click.option(
            "--package-name",
            multiple=allow_multiple,
            help="Specify Python package where repository or job function lives",
            envvar="DAGSTER_PACKAGE_NAME",
        ),
        click.option(
            "--attribute",
            "-a",
            help=(
                "Attribute that is either a 1) repository or job or "
                "2) a function that returns a repository or job"
            ),
            envvar="DAGSTER_ATTRIBUTE",
        ),
    ]


def _generate_grpc_server_options(hidden=False) -> Sequence[ClickOption]:
    return [
        click.option(
            "--grpc-port",
            type=click.INT,
            required=False,
            help="Port to use to connect to gRPC server",
            hidden=hidden,
        ),
        click.option(
            "--grpc-socket",
            type=click.Path(),
            required=False,
            help="Named socket to use to connect to gRPC server",
            hidden=hidden,
        ),
        click.option(
            "--grpc-host",
            type=click.STRING,
            required=False,
            help="Host to use to connect to gRPC server, defaults to localhost",
            hidden=hidden,
        ),
        click.option(
            "--use-ssl",
            is_flag=True,
            default=False,
            help="Use a secure channel when connecting to the gRPC server",
            hidden=hidden,
        ),
    ]


def _generate_workspace_options() -> Sequence[ClickOption]:
    return [
        click.option("--empty-workspace", is_flag=True, help="Allow an empty workspace"),
        click.option(
            "--workspace",
            "-w",
            multiple=True,
            type=click.Path(exists=True),
            help="Path to workspace file. Argument can be provided multiple times.",
        ),
        *_generate_python_pointer_options(allow_multiple=True),
        *_generate_grpc_server_options(),
    ]


def _get_code_pointer_dict_from_python_pointer_opts(
    params: PythonPointerOpts,
) -> Mapping[str, CodePointer]:
    working_directory = params.working_directory or os.getcwd()
    loadable_targets = get_loadable_targets(
        params.python_file,
        params.module_name,
        params.package_name,
        working_directory,
        params.attribute,
    )

    # repository_name -> code_pointer
    code_pointer_dict: dict[str, CodePointer] = {}
    for loadable_target in loadable_targets:
        repo_def = check.not_none(repository_def_from_target_def(loadable_target.target_definition))
        if params.python_file:
            code_pointer = CodePointer.from_python_file(
                params.python_file, loadable_target.attribute, working_directory
            )
        elif params.module_name:
            code_pointer = CodePointer.from_module(
                params.module_name, loadable_target.attribute, working_directory
            )
        elif params.package_name:
            code_pointer = CodePointer.from_python_package(
                params.package_name, loadable_target.attribute, working_directory
            )
        else:
            check.failed("Must specify a Python file or module name")

        code_pointer_dict[repo_def.name] = code_pointer

    return code_pointer_dict


def get_repository_python_origin_from_cli_opts(
    params: PythonPointerOpts, repo_name: Optional[str] = None
) -> RepositoryPythonOrigin:
    if sum([bool(x) for x in (params.python_file, params.module_name, params.package_name)]) != 1:
        _raise_cli_usage_error()

    # Short-circuit the case where an attribute and no repository name is passed in,
    # giving us enough information to return an origin without loading any target
    # definitions - we may need to return an origin for a non-existent repository
    # (e.g. to log an origin ID for an error message)
    if params.attribute and not repo_name:
        working_directory = params.working_directory or os.getcwd()
        if params.python_file:
            code_pointer: CodePointer = CodePointer.from_python_file(
                params.python_file,
                params.attribute,
                working_directory,
            )
        elif params.module_name:
            code_pointer = CodePointer.from_module(
                params.module_name,
                params.attribute,
                working_directory,
            )
        elif params.package_name:
            code_pointer = CodePointer.from_python_package(
                params.package_name,
                params.attribute,
                working_directory,
            )
        else:
            check.failed("Must specify a Python file or module name")
        return RepositoryPythonOrigin(
            executable_path=sys.executable,
            code_pointer=code_pointer,
            entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
        )

    code_pointer_dict = _get_code_pointer_dict_from_python_pointer_opts(params)
    found_repo_names = serialize_sorted_quoted(code_pointer_dict.keys())
    if repo_name is None and len(code_pointer_dict) == 1:
        code_pointer = next(iter(code_pointer_dict.values()))
    elif repo_name is None:
        raise click.UsageError(
            "Must provide --repository as there is more than one repository. "
            f"Options are: {found_repo_names}."
        )
    elif repo_name not in code_pointer_dict:
        raise click.UsageError(
            f'Repository "{repo_name}" not found. Found {found_repo_names} instead.'
        )
    else:
        code_pointer = code_pointer_dict[repo_name]

    return RepositoryPythonOrigin(
        executable_path=sys.executable,
        code_pointer=code_pointer,
        entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
    )


def get_code_location_from_workspace(
    workspace: WorkspaceRequestContext, code_location_name: Optional[str]
) -> CodeLocation:
    if code_location_name is None:
        if len(workspace.code_location_names) == 1:
            code_location_name = workspace.code_location_names[0]
        elif len(workspace.code_location_names) == 0:
            raise click.UsageError("No locations found in workspace")
        elif code_location_name is None:
            raise click.UsageError(
                "Must provide --location as there are multiple locations "
                f"available. Options are: {serialize_sorted_quoted(workspace.code_location_names)}"
            )

    if code_location_name not in workspace.code_location_names:
        raise click.UsageError(
            f'Location "{code_location_name}" not found in workspace. '
            f"Found {serialize_sorted_quoted(workspace.code_location_names)} instead."
        )

    if workspace.has_code_location_error(code_location_name):
        raise click.UsageError(
            f'Error loading location "{code_location_name}": {workspace.get_code_location_error(code_location_name)!s}'
        )

    return workspace.get_code_location(code_location_name)


def get_remote_repository_from_code_location(
    code_location: CodeLocation, provided_repo_name: Optional[str]
) -> RemoteRepository:
    check.inst_param(code_location, "code_location", CodeLocation)
    check.opt_str_param(provided_repo_name, "provided_repo_name")

    repo_dict = code_location.get_repositories()
    check.invariant(repo_dict, "There should be at least one repo.")

    # no name provided and there is only one repo. Automatically return
    if provided_repo_name is None and len(repo_dict) == 1:
        return next(iter(repo_dict.values()))

    if provided_repo_name is None:
        raise click.UsageError(
            "Must provide --repository as there is more than one repository "
            f"in {code_location.name}. Options are: {serialize_sorted_quoted(repo_dict.keys())}."
        )

    if not code_location.has_repository(provided_repo_name):
        raise click.UsageError(
            f'Repository "{provided_repo_name}" not found in location "{code_location.name}". '
            f"Found {serialize_sorted_quoted(repo_dict.keys())} instead."
        )

    return code_location.get_repository(provided_repo_name)


def get_remote_job_from_remote_repo(
    remote_repo: RemoteRepository,
    provided_name: Optional[str],
) -> RemoteJob:
    check.inst_param(remote_repo, "remote_repo", RemoteRepository)
    check.opt_str_param(provided_name, "provided_name")

    remote_jobs = {ep.name: ep for ep in (remote_repo.get_all_jobs())}

    check.invariant(remote_jobs)

    if provided_name is None and len(remote_jobs) == 1:
        return next(iter(remote_jobs.values()))

    if provided_name is None:
        raise click.UsageError(
            "Must provide --job as there is more than one job "
            f"in {remote_repo.name}. Options are: {serialize_sorted_quoted(remote_jobs.keys())}."
        )

    if provided_name not in remote_jobs:
        raise click.UsageError(
            f'Job "{provided_name}" not found in repository "{remote_repo.name}". '
            f"Found {serialize_sorted_quoted(remote_jobs.keys())} instead."
        )

    return remote_jobs[provided_name]


def get_run_config_from_file_list(file_list: list[str]) -> Mapping[str, object]:
    check.opt_sequence_param(file_list, "file_list", of_type=str)
    return cast(Mapping[str, object], load_yaml_from_glob_list(file_list) if file_list else {})


def get_run_config_from_cli_opts(
    config_files: tuple[str, ...], config_json: Optional[str]
) -> Mapping[str, object]:
    if not (config_files or config_json):
        return {}
    elif config_files and config_json:
        raise click.UsageError("Cannot specify both -c / --config and --config-json")
    elif config_files:
        return get_run_config_from_file_list(list(config_files))
    elif config_json:
        try:
            return json.loads(config_json)
        except JSONDecodeError:
            raise click.UsageError(
                f"Invalid JSON-string given for `--config-json`: {config_json}\n\n{serializable_error_info_from_exc_info(sys.exc_info()).to_string()}"
            )
    else:
        check.failed("Unhandled case getting config from kwargs")


# ########################
# ##### HELPERS
# ########################


def _raise_cli_usage_error(msg: Optional[str] = None) -> Never:
    raise UsageError(
        msg or "Invalid set of CLI arguments for loading repository/job. See --help for details."
    )


def _check_attrs_falsey(obj: object, *attrs: str) -> None:
    if not _are_attrs_falsey(obj, *attrs):
        _raise_cli_usage_error()


def _are_attrs_falsey(obj: object, *attrs: str) -> bool:
    for attr in attrs:
        if getattr(obj, attr):
            return False
    return True
