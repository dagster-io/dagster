import os
import sys
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import click
import tomli
from click import UsageError
from typing_extensions import Never, TypeAlias

import dagster._check as check
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.reconstruct import repository_def_from_target_def
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.host_representation.code_location import CodeLocation
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.instance import DagsterInstance
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    JobPythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._core.workspace.load_target import (
    CompositeTarget,
    EmptyWorkspaceTarget,
    GrpcServerTarget,
    ModuleTarget,
    PackageTarget,
    PyProjectFileTarget,
    PythonFileTarget,
    WorkspaceFileTarget,
    WorkspaceLoadTarget,
)
from dagster._grpc.utils import get_loadable_targets
from dagster._utils.hosted_user_process import recon_repository_from_origin

if TYPE_CHECKING:
    from dagster._core.workspace.context import WorkspaceProcessContext

from dagster._core.host_representation.external import ExternalJob

WORKSPACE_TARGET_WARNING = (
    "Can only use ONE of --workspace/-w, --python-file/-f, --module-name/-m, --grpc-port,"
    " --grpc-socket."
)

T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])

ClickArgValue: TypeAlias = Union[str, Tuple[str]]
ClickArgMapping: TypeAlias = Mapping[str, ClickArgValue]
ClickOption: TypeAlias = Callable[[T_Callable], T_Callable]


def _raise_cli_usage_error(msg: Optional[str] = None) -> Never:
    raise UsageError(
        msg or "Invalid set of CLI arguments for loading repository/job. See --help for details."
    )


def _check_cli_arguments_none(kwargs: ClickArgMapping, *keys: str) -> None:
    for key in keys:
        if kwargs.get(key):
            _raise_cli_usage_error()


def are_all_keys_empty(kwargs: ClickArgMapping, keys: Iterable[str]) -> bool:
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


def _has_pyproject_dagster_block(path: str) -> bool:
    if not os.path.exists(path):
        return False
    with open(path, "rb") as f:
        data = tomli.load(f)
        if not isinstance(data, dict):
            return False

        return "dagster" in data.get("tool", {})


def get_workspace_load_target(kwargs: ClickArgMapping) -> WorkspaceLoadTarget:
    check.mapping_param(kwargs, "kwargs")
    if are_all_keys_empty(kwargs, WORKSPACE_CLI_ARGS):
        if kwargs.get("empty_workspace"):
            return EmptyWorkspaceTarget()
        if _has_pyproject_dagster_block("pyproject.toml"):
            return PyProjectFileTarget("pyproject.toml")

        if os.path.exists("workspace.yaml"):
            return WorkspaceFileTarget(paths=["workspace.yaml"])
        raise click.UsageError(
            "No arguments given and no [tool.dagster] block in pyproject.toml found."
        )

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
        python_files = kwargs["python_file"]

        working_directory = get_working_directory_from_kwargs(kwargs)

        if len(python_files) == 1:
            return PythonFileTarget(
                python_file=python_files[0],
                attribute=check.opt_str_elem(kwargs, "attribute"),
                working_directory=working_directory,
                location_name=None,
            )
        else:
            # multiple files

            if kwargs.get("attribute"):
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
                    for python_file in python_files
                ]
            )

    if kwargs.get("module_name"):
        _check_cli_arguments_none(
            kwargs,
            "package_name",
            "grpc_host",
            "grpc_port",
            "grpc_socket",
        )

        module_names = kwargs["module_name"]

        check.is_tuple(module_names, of_type=str)

        working_directory = get_working_directory_from_kwargs(kwargs)

        if len(module_names) == 1:
            return ModuleTarget(
                module_name=module_names[0],
                attribute=check.opt_str_elem(kwargs, "attribute"),
                working_directory=working_directory,
                location_name=None,
            )
        else:
            # multiple modules

            if kwargs.get("attribute"):
                raise UsageError(
                    "If you are specifying multiple modules you cannot specify an attribute. Got"
                    f" modules {module_names}."
                )

            return CompositeTarget(
                targets=[
                    ModuleTarget(
                        module_name=module_name,
                        attribute=None,
                        working_directory=working_directory,
                        location_name=None,
                    )
                    for module_name in module_names
                ]
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
        _raise_cli_usage_error()


def get_workspace_process_context_from_kwargs(
    instance: DagsterInstance,
    version: str,
    read_only: bool,
    kwargs: ClickArgMapping,
    code_server_log_level: str = "INFO",
) -> "WorkspaceProcessContext":
    from dagster._core.workspace.context import WorkspaceProcessContext

    return WorkspaceProcessContext(
        instance,
        get_workspace_load_target(kwargs),
        version=version,
        read_only=read_only,
        code_server_log_level=code_server_log_level,
    )


@contextmanager
def get_workspace_from_kwargs(
    instance: DagsterInstance,
    version: str,
    kwargs: ClickArgMapping,
) -> Iterator[WorkspaceRequestContext]:
    with get_workspace_process_context_from_kwargs(
        instance, version, read_only=False, kwargs=kwargs
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def python_file_option(allow_multiple: bool) -> ClickOption:
    return click.option(
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
    )


def workspace_option() -> ClickOption:
    return click.option(
        "--workspace",
        "-w",
        multiple=True,
        type=click.Path(exists=True),
        help="Path to workspace file. Argument can be provided multiple times.",
    )


def python_module_option(allow_multiple: bool) -> ClickOption:
    return click.option(
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
    )


def working_directory_option() -> ClickOption:
    return click.option(
        "--working-directory",
        "-d",
        help="Specify working directory to use when loading the repository or job",
        envvar="DAGSTER_WORKING_DIRECTORY",
    )


def python_target_click_options(allow_multiple_python_targets: bool) -> Sequence[ClickOption]:
    return [
        working_directory_option(),
        python_file_option(allow_multiple=allow_multiple_python_targets),
        python_module_option(allow_multiple=allow_multiple_python_targets),
        click.option(
            "--package-name",
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


def grpc_server_target_click_options(hidden=False) -> Sequence[ClickOption]:
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
            required=False,
            help="Use a secure channel when connecting to the gRPC server",
            hidden=hidden,
        ),
    ]


def workspace_target_click_options() -> Sequence[ClickOption]:
    return [
        click.option("--empty-workspace", is_flag=True, help="Allow an empty workspace"),
        workspace_option(),
        *python_target_click_options(allow_multiple_python_targets=True),
        *grpc_server_target_click_options(),
    ]


def python_job_target_click_options() -> Sequence[ClickOption]:
    return [
        *python_target_click_options(allow_multiple_python_targets=False),
        click.option(
            "--repository",
            "-r",
            help="Repository name, necessary if more than one repository is present.",
        ),
        job_option(),
    ]


def target_with_config_option(command_name: str) -> ClickOption:
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
            f"dagster job {command_name} -f hello_world.py -j pandas_hello_world "
            '-c "pandas_hello_world/*.yaml"'
            "\n\nYou can also specify multiple files:"
            "\n\nExample: "
            f"dagster job {command_name} -f hello_world.py -j pandas_hello_world "
            "-c pandas_hello_world/ops.yaml -c pandas_hello_world/env.yaml"
        ),
    )


def python_job_config_argument(command_name: str) -> Callable[[T_Callable], T_Callable]:
    def wrap(f: T_Callable) -> T_Callable:
        return target_with_config_option(command_name)(f)

    return wrap


def python_job_target_argument(f):
    from dagster._cli.job import apply_click_params

    return apply_click_params(f, *python_job_target_click_options())


def workspace_target_argument(f):
    from dagster._cli.job import apply_click_params

    return apply_click_params(f, *workspace_target_click_options())


def job_workspace_target_argument(f):
    from dagster._cli.job import apply_click_params

    return apply_click_params(f, *workspace_target_click_options())


def grpc_server_origin_target_argument(f):
    from dagster._cli.job import apply_click_params

    options = grpc_server_target_click_options()
    return apply_click_params(f, *options)


def python_origin_target_argument(f):
    from dagster._cli.job import apply_click_params

    options = python_target_click_options(allow_multiple_python_targets=False)
    return apply_click_params(f, *options)


def repository_click_options() -> Sequence[ClickOption]:
    return [
        click.option(
            "--repository",
            "-r",
            help=(
                "Name of the repository, necessary if more than one repository is present in the"
                " code location."
            ),
        ),
        click.option(
            "--location",
            "-l",
            help="Name of the code location, necessary if more than one location is present.",
        ),
    ]


def repository_target_argument(f):
    from dagster._cli.job import apply_click_params

    return apply_click_params(workspace_target_argument(f), *repository_click_options())


def job_repository_target_argument(f: T_Callable) -> T_Callable:
    from dagster._cli.job import apply_click_params

    return apply_click_params(job_workspace_target_argument(f), *repository_click_options())


def job_option() -> ClickOption:
    return click.option(
        "--job",
        "-j",
        "job_name",
        help="Job within the repository, necessary if more than one job is present.",
    )


def job_target_argument(f: T_Callable) -> T_Callable:
    from dagster._cli.job import apply_click_params

    return apply_click_params(job_repository_target_argument(f), job_option())


def get_job_python_origin_from_kwargs(kwargs: ClickArgMapping) -> JobPythonOrigin:
    repository_origin = get_repository_python_origin_from_kwargs(kwargs)
    provided_name = kwargs.get("job_name")

    recon_repo = recon_repository_from_origin(repository_origin)
    repo_definition = recon_repo.get_definition()

    job_names = set(repo_definition.job_names)  # job (all) vs job (non legacy)

    if provided_name is None and len(job_names) == 1:
        job_name = next(iter(job_names))
    elif provided_name is None:
        raise click.UsageError(
            "Must provide --job as there is more than one job "
            f"in {repo_definition.name}. Options are: {_sorted_quoted(job_names)}."
        )
    elif provided_name not in job_names:
        raise click.UsageError(
            f'Job "{provided_name}" not found in repository "{repo_definition.name}" '
            f"Found {_sorted_quoted(job_names)} instead."
        )
    else:
        job_name = provided_name

    return JobPythonOrigin(job_name, repository_origin=repository_origin)


def _get_code_pointer_dict_from_kwargs(kwargs: ClickArgMapping) -> Mapping[str, CodePointer]:
    python_file = check.opt_str_elem(kwargs, "python_file")
    module_name = check.opt_str_elem(kwargs, "module_name")
    package_name = check.opt_str_elem(kwargs, "package_name")
    working_directory = get_working_directory_from_kwargs(kwargs)
    attribute = check.opt_str_elem(kwargs, "attribute")
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


def get_working_directory_from_kwargs(kwargs: ClickArgMapping) -> Optional[str]:
    return check.opt_str_elem(kwargs, "working_directory") or os.getcwd()


def get_repository_python_origin_from_kwargs(kwargs: ClickArgMapping) -> RepositoryPythonOrigin:
    provided_repo_name = check.opt_str_elem(kwargs, "repository")

    if not (kwargs.get("python_file") or kwargs.get("module_name") or kwargs.get("package_name")):
        raise click.UsageError("Must specify a python file or module name")

    # Short-circuit the case where an attribute and no repository name is passed in,
    # giving us enough information to return an origin without loading any target
    # definitions - we may need to return an origin for a non-existent repository
    # (e.g. to log an origin ID for an error message)
    if kwargs.get("attribute") and not provided_repo_name:
        if kwargs.get("python_file"):
            _check_cli_arguments_none(kwargs, "module_name", "package_name")
            python_file = check.str_elem(kwargs, "python_file")
            code_pointer: CodePointer = CodePointer.from_python_file(
                python_file,
                check.str_elem(kwargs, "attribute"),
                get_working_directory_from_kwargs(kwargs),
            )
        elif kwargs.get("module_name"):
            _check_cli_arguments_none(kwargs, "python_file", "package_name")
            module_name = check.str_elem(kwargs, "module_name")
            code_pointer = CodePointer.from_module(
                module_name,
                check.str_elem(kwargs, "attribute"),
                get_working_directory_from_kwargs(kwargs),
            )
        elif kwargs.get("package_name"):
            _check_cli_arguments_none(kwargs, "python_file", "module_name")
            code_pointer = CodePointer.from_python_package(
                check.str_elem(kwargs, "package_name"),
                check.str_elem(kwargs, "attribute"),
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
            "Must provide --repository as there is more than one repository. "
            f"Options are: {found_repo_names}."
        )
    elif provided_repo_name not in code_pointer_dict:
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
def get_code_location_from_kwargs(
    instance: DagsterInstance, version: str, kwargs: ClickArgMapping
) -> Iterator[CodeLocation]:
    # Instance isn't strictly required to load a repository location, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_workspace_from_kwargs(instance, version, kwargs) as workspace:
        location_name = check.opt_str_elem(kwargs, "location")
        yield get_code_location_from_workspace(workspace, location_name)


def get_code_location_from_workspace(
    workspace: WorkspaceRequestContext, provided_location_name: Optional[str]
) -> CodeLocation:
    if provided_location_name is None:
        if len(workspace.code_location_names) == 1:
            provided_location_name = workspace.code_location_names[0]
        elif len(workspace.code_location_names) == 0:
            raise click.UsageError("No locations found in workspace")
        elif provided_location_name is None:
            raise click.UsageError(
                "Must provide --location as there are multiple locations "
                f"available. Options are: {_sorted_quoted(workspace.code_location_names)}"
            )

    if provided_location_name not in workspace.code_location_names:
        raise click.UsageError(
            f'Location "{provided_location_name}" not found in workspace. '
            f"Found {_sorted_quoted(workspace.code_location_names)} instead."
        )

    if workspace.has_code_location_error(provided_location_name):
        raise click.UsageError(
            'Error loading location "{provided_location_name}": {error_str}'.format(
                provided_location_name=provided_location_name,
                error_str=str(workspace.get_code_location_error(provided_location_name)),
            )
        )

    return workspace.get_code_location(provided_location_name)


def get_external_repository_from_code_location(
    code_location: CodeLocation, provided_repo_name: Optional[str]
) -> ExternalRepository:
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
            f"in {code_location.name}. Options are: {_sorted_quoted(repo_dict.keys())}."
        )

    if not code_location.has_repository(provided_repo_name):
        raise click.UsageError(
            f'Repository "{provided_repo_name}" not found in location "{code_location.name}". '
            f"Found {_sorted_quoted(repo_dict.keys())} instead."
        )

    return code_location.get_repository(provided_repo_name)


@contextmanager
def get_external_repository_from_kwargs(
    instance: DagsterInstance, version: str, kwargs: ClickArgMapping
) -> Iterator[ExternalRepository]:
    # Instance isn't strictly required to load an ExternalRepository, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_code_location_from_kwargs(instance, version, kwargs) as code_location:
        provided_repo_name = check.opt_str_elem(kwargs, "repository")
        yield get_external_repository_from_code_location(code_location, provided_repo_name)


def get_external_job_from_external_repo(
    external_repo: ExternalRepository,
    provided_name: Optional[str],
) -> ExternalJob:
    check.inst_param(external_repo, "external_repo", ExternalRepository)
    check.opt_str_param(provided_name, "provided_name")

    external_jobs = {ep.name: ep for ep in (external_repo.get_all_external_jobs())}

    check.invariant(external_jobs)

    if provided_name is None and len(external_jobs) == 1:
        return next(iter(external_jobs.values()))

    if provided_name is None:
        raise click.UsageError(
            "Must provide --job as there is more than one job "
            f"in {external_repo.name}. Options are: {_sorted_quoted(external_jobs.keys())}."
        )

    if provided_name not in external_jobs:
        raise click.UsageError(
            f'Job "{provided_name}" not found in repository "{external_repo.name}". '
            f"Found {_sorted_quoted(external_jobs.keys())} instead."
        )

    return external_jobs[provided_name]


@contextmanager
def get_external_job_from_kwargs(instance: DagsterInstance, version: str, kwargs: ClickArgMapping):
    # Instance isn't strictly required to load an ExternalJob, but is included
    # to satisfy the WorkspaceProcessContext / WorkspaceRequestContext requirements
    with get_external_repository_from_kwargs(instance, version, kwargs) as external_repo:
        provided_name = check.opt_str_elem(kwargs, "job_name")
        yield get_external_job_from_external_repo(external_repo, provided_name)


def _sorted_quoted(strings: Iterable[str]) -> str:
    return "[" + ", ".join([f"'{s}'" for s in sorted(list(strings))]) + "]"
