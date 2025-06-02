from collections.abc import Sequence
from typing import Any, Callable, Optional, TypeVar

import click
from typing_extensions import Self, TypeAlias

from dagster_shared.record import as_dict, record

T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])

ClickOption: TypeAlias = Callable[[T_Callable], T_Callable]


def apply_click_params(command: T_Callable, *click_params: ClickOption) -> T_Callable:
    for click_param in click_params:
        command = click_param(command)
    return command


def python_pointer_options(f: T_Callable) -> T_Callable:
    return apply_click_params(
        f,
        *generate_python_pointer_options(
            allow_multiple=False,
            hide_legacy_options=False,
        ),
    )


def generate_python_pointer_options(
    *,
    allow_multiple: bool,
    hide_legacy_options: bool,
) -> Sequence[ClickOption]:
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
            "--autoload-defs-module-name",
            help=("A module to import and recursively search through for definitions."),
            envvar="DAGSTER_autoload_defs_module_name",
        ),
        click.option(
            "--package-name",
            multiple=allow_multiple,
            help="Specify Python package where repository or job function lives",
            envvar="DAGSTER_PACKAGE_NAME",
            hidden=hide_legacy_options,
        ),
        click.option(
            "--attribute",
            "-a",
            help=(
                "Attribute that is either a 1) repository or job or "
                "2) a function that returns a repository or job"
            ),
            envvar="DAGSTER_ATTRIBUTE",
            hidden=hide_legacy_options,
        ),
    ]


def generate_grpc_server_options() -> Sequence[ClickOption]:
    return []


def generate_workspace_options(*, hide_uncommon_options: bool) -> Sequence[ClickOption]:
    return [
        click.option("--empty-workspace", is_flag=True, help="Allow an empty workspace"),
        click.option(
            "--workspace",
            "-w",
            multiple=True,
            type=click.Path(exists=True),
            help="Path to workspace file. Argument can be provided multiple times.",
        ),
        *generate_python_pointer_options(
            allow_multiple=True,
            hide_legacy_options=hide_uncommon_options,
        ),
        click.option(
            "--grpc-port",
            type=click.INT,
            required=False,
            help="Port to use to connect to gRPC server",
            hidden=hide_uncommon_options,
        ),
        click.option(
            "--grpc-socket",
            type=click.Path(),
            required=False,
            help="Named socket to use to connect to gRPC server",
            hidden=hide_uncommon_options,
        ),
        click.option(
            "--grpc-host",
            type=click.STRING,
            required=False,
            help="Host to use to connect to gRPC server, defaults to localhost",
            hidden=hide_uncommon_options,
        ),
        click.option(
            "--use-ssl",
            is_flag=True,
            default=False,
            help="Use a secure channel when connecting to the gRPC server",
            hidden=hide_uncommon_options,
        ),
    ]


def dg_workspace_options(f: T_Callable) -> T_Callable:
    return apply_click_params(
        f,
        *generate_workspace_options(
            hide_uncommon_options=True,  # dg as a newer cli hides deprecated and rarely used options
        ),
    )


def workspace_options(f: T_Callable) -> T_Callable:
    return apply_click_params(
        f,
        *generate_workspace_options(
            hide_uncommon_options=False,
        ),
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

    autoload_defs_module_name: Optional[str] = None

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
            empty_workspace=cli_options.pop("empty_workspace", False),
            workspace=cli_options.pop("workspace", None),
            python_file=cli_options.pop("python_file", None),
            module_name=cli_options.pop("module_name", None),
            package_name=cli_options.pop("package_name", None),
            working_directory=cli_options.pop("working_directory", None),
            attribute=cli_options.pop("attribute", None),
            autoload_defs_module_name=cli_options.pop("autoload_defs_module_name", None),
            grpc_port=cli_options.pop("grpc_port", None),
            grpc_socket=cli_options.pop("grpc_socket", None),
            grpc_host=cli_options.pop("grpc_host", None),
            use_ssl=cli_options.pop("use_ssl", False),
        )

    def specifies_target(self) -> bool:
        set_args = [
            k for k, v in as_dict(self).items() if v and (k not in {"empty_workspace", "use_ssl"})
        ]
        return bool(set_args)


@record
class PythonPointerOpts:
    python_file: Optional[str] = None
    module_name: Optional[str] = None
    package_name: Optional[str] = None
    working_directory: Optional[str] = None
    attribute: Optional[str] = None
    autoload_defs_module_name: Optional[str] = None

    @classmethod
    def extract_from_cli_options(cls, cli_options: dict[str, Any]) -> Self:
        # This is expected to always be called from a click entry point, so all options should be
        # present in the dictionary. We rely on `@record` for type-checking.
        return cls(
            python_file=cli_options.pop("python_file", None),
            module_name=cli_options.pop("module_name", None),
            package_name=cli_options.pop("package_name", None),
            working_directory=cli_options.pop("working_directory", None),
            attribute=cli_options.pop("attribute", None),
            autoload_defs_module_name=cli_options.pop("autoload_defs_module_name", None),
        )

    def to_workspace_opts(self) -> "WorkspaceOpts":
        return WorkspaceOpts(
            python_file=(self.python_file,) if self.python_file else None,
            module_name=(self.module_name,) if self.module_name else None,
            package_name=(self.package_name,) if self.package_name else None,
            autoload_defs_module_name=self.autoload_defs_module_name
            if self.autoload_defs_module_name
            else None,
            working_directory=self.working_directory,
            attribute=self.attribute,
        )

    def specifies_target(self) -> bool:
        return bool(self.python_file or self.module_name or self.package_name)
