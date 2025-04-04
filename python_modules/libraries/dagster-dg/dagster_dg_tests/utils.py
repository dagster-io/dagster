import contextlib
import os
import shutil
import socket
import subprocess
import sys
import traceback
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Any, Literal, Optional, Union

import click
import tomlkit
import tomlkit.items
from click.testing import CliRunner, Result
from dagster_dg.cli import (
    DG_CLI_MAX_OUTPUT_WIDTH,
    cli,
    cli as dg_cli,
)
from dagster_dg.config import is_dg_specific_config_file
from dagster_dg.utils import (
    create_toml_node,
    delete_toml_node,
    discover_git_root,
    get_toml_node,
    get_venv_executable,
    has_toml_node,
    install_to_venv,
    is_windows,
    modify_toml,
    modify_toml_as_dict,
    pushd,
    set_toml_node,
)
from typing_extensions import Self, TypeAlias

STANDARD_TEST_COMPONENT_MODULE = "dagster_test.components"


def crawl_cli_commands() -> dict[tuple[str, ...], click.Command]:
    """Note that this does not pick up:
    - all `scaffold` subcommands, because these are dynamically generated and vary across
      environment.
    - special --ACTION options with callbacks (e.g. `--rebuild-component-registry`).
    """
    commands: dict[tuple[str, ...], click.Command] = {}

    def _crawl(command: click.Command, path: tuple[str, ...]):
        assert command.name
        new_path = (*path, command.name)
        if isinstance(command, click.Group):
            for subcommand in command.commands.values():
                assert subcommand.name
                _crawl(subcommand, new_path)
        else:
            commands[new_path] = command

    _crawl(cli, tuple())

    return commands


def _install_libraries_to_venv(venv_path: Path, libraries_rel_paths: Sequence[str]) -> None:
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    install_args: list[str] = []
    for path in libraries_rel_paths:
        full_path = Path(dagster_git_repo_dir) / "python_modules" / path
        install_args.extend(["-e", str(full_path)])
    install_to_venv(venv_path, install_args)


@contextmanager
def isolated_components_venv(runner: Union[CliRunner, "ProxyRunner"]) -> Iterator[Path]:
    with runner.isolated_filesystem():
        subprocess.run(["uv", "venv", ".venv"], check=True)
        venv_path = Path.cwd() / ".venv"
        _install_libraries_to_venv(
            venv_path,
            [
                "dagster",
                "dagster-pipes",
                "libraries/dagster-shared",
                "dagster-test",
            ],
        )

        venv_exec_path = get_venv_executable(venv_path).parent
        assert (venv_exec_path / "python").exists() or (venv_exec_path / "python.exe").exists()
        with modify_environment_variable(
            "PATH", os.pathsep.join([str(venv_exec_path), os.environ["PATH"]])
        ):
            yield venv_path


@contextmanager
def isolated_dg_venv(runner: Union[CliRunner, "ProxyRunner"]) -> Iterator[Path]:
    with runner.isolated_filesystem():
        subprocess.run(["uv", "venv", ".venv"], check=True)
        venv_path = Path.cwd() / ".venv"
        _install_libraries_to_venv(
            venv_path,
            [
                "libraries/dagster-dg",
                "libraries/dagster-shared",
            ],
        )

        venv_exec_path = get_venv_executable(venv_path).parent
        assert (venv_exec_path / "python").exists() or (venv_exec_path / "python.exe").exists()
        with modify_environment_variable(
            "PATH", os.pathsep.join([str(venv_exec_path), os.environ["PATH"]])
        ):
            yield venv_path


ConfigFileType: TypeAlias = Literal["dg.toml", "pyproject.toml"]
PackageLayoutType: TypeAlias = Literal["root", "src"]


@contextmanager
def isolated_example_workspace(
    runner: Union[CliRunner, "ProxyRunner"],
    project_name: Optional[str] = None,
    create_venv: bool = False,
    use_editable_dagster: bool = True,
    workspace_config_file_type: ConfigFileType = "dg.toml",
    project_config_file_type: ConfigFileType = "pyproject.toml",
) -> Iterator[None]:
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        runner.isolated_filesystem(),
        clear_module_from_cache("foo_bar"),
        clear_module_from_cache(project_name) if project_name else nullcontext(),
    ):
        result = runner.invoke(
            "scaffold",
            "workspace",
            "dagster-workspace",
            *(["--use-editable-dagster", dagster_git_repo_dir] if use_editable_dagster else []),
        )
        assert_runner_result(result)
        if workspace_config_file_type == "pyproject.toml":
            convert_dg_toml_to_pyproject_toml(
                Path("dagster-workspace") / "dg.toml",
                Path("dagster-workspace") / "pyproject.toml",
            )
        with pushd("dagster-workspace"):
            if project_name:
                result = runner.invoke(
                    "scaffold",
                    "project",
                    "projects/" + project_name,
                    *(
                        ["--use-editable-dagster", dagster_git_repo_dir]
                        if use_editable_dagster
                        else []
                    ),
                )
                assert_runner_result(result)
                if project_config_file_type == "dg.toml":
                    convert_pyproject_toml_to_dg_toml(
                        Path("projects") / project_name / "pyproject.toml",
                        Path("projects") / project_name / "dg.toml",
                    )

            # Create a venv capable of running dagster dev
            if create_venv:
                subprocess.run(["uv", "venv", ".venv"], check=True)
                venv_path = Path.cwd() / ".venv"
                _install_libraries_to_venv(
                    venv_path,
                    [
                        "dagster",
                        "dagster-webserver",
                        "dagster-graphql",
                        "dagster-test",
                        "dagster-pipes",
                        "libraries/dagster-shared",
                    ],
                )
            yield


# Preferred example project is foo-bar instead of a single word so that we can test the effect
# of hyphenation.
@contextmanager
def isolated_example_project_foo_bar(
    runner: Union[CliRunner, "ProxyRunner"],
    in_workspace: bool = True,
    skip_venv: bool = False,
    populate_cache: bool = False,
    component_dirs: Sequence[Path] = [],
    config_file_type: ConfigFileType = "pyproject.toml",
    package_layout: PackageLayoutType = "src",
) -> Iterator[None]:
    """Scaffold a project named foo_bar in an isolated filesystem.

    Args:
        runner: The runner to use for invoking commands.
        in_workspace: Whether the project should be scaffolded inside a workspace directory.
        skip_venv: Whether to skip creating a virtual environment when scaffolding the project.
        component_dirs: A list of component directories that will be copied into the project component root.
    """
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    project_path = Path("foo-bar")
    if in_workspace:
        fs_context = isolated_example_workspace(runner)
    else:
        fs_context = runner.isolated_filesystem()
    with fs_context:
        args = [
            "scaffold",
            "project",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            *(["--skip-venv"] if skip_venv else []),
            *(["--no-populate-cache"] if not populate_cache else []),
            "foo-bar",
        ]
        result = runner.invoke(*args)

        assert_runner_result(result)
        if config_file_type == "dg.toml":
            convert_pyproject_toml_to_dg_toml(
                Path("foo-bar") / "pyproject.toml",
                Path("foo-bar") / "dg.toml",
            )
        if package_layout == "root":
            # Move the src directory to the root of the project
            curr_pkg_root = Path("foo-bar") / "src" / "foo_bar"
            new_pkg_root = Path("foo-bar") / "foo_bar"
            shutil.move(curr_pkg_root, new_pkg_root)
            Path("foo-bar", "src").rmdir()

            with modify_toml_as_dict(Path("foo-bar/pyproject.toml")) as toml:
                create_toml_node(toml, ("tool", "hatch", "build", "packages"), ["foo_bar"])

            # Reinstall to venv since package root changed
            install_to_venv(Path("foo-bar/.venv"), ["-e", "foo-bar"])

        with clear_module_from_cache("foo_bar"), pushd(project_path):
            # _install_libraries_to_venv(Path(".venv"), ["dagster-test"])
            for src_dir in component_dirs:
                component_name = src_dir.name
                components_dir = Path.cwd() / "src" / "foo_bar" / "defs" / component_name
                components_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_dir, components_dir, dirs_exist_ok=True)
            yield


@contextmanager
def isolated_example_component_library_foo_bar(
    runner: Union[CliRunner, "ProxyRunner"],
    lib_module_name: Optional[str] = None,
    skip_venv: bool = False,
) -> Iterator[None]:
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        (
            runner.isolated_filesystem() if skip_venv else isolated_components_venv(runner)
        ) as venv_path,
        # clear_module_from_cache("foo_bar"),
    ):
        # We just use the project generation function and then modify it to be a component library
        # only.
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "--skip-venv",
            "foo-bar",
        )
        assert_runner_result(result)
        with clear_module_from_cache("foo_bar"), pushd("foo-bar"):
            shutil.rmtree(Path("src/foo_bar/defs"))

            # Make it not a project
            with modify_toml(Path("pyproject.toml")) as toml:
                delete_toml_node(toml, ("tool", "dg"))

                # We need to set any alternative lib package name _before_ we install into the
                # environment, since it affects entry points which are set at install time.
                if lib_module_name:
                    set_toml_node(
                        toml,
                        ("project", "entry-points", "dagster_dg.library", "foo_bar"),
                        lib_module_name,
                    )
                    Path("src", *lib_module_name.split(".")).mkdir(exist_ok=True)

            # Install the component library into our venv
            if not skip_venv:
                assert venv_path
                install_to_venv(venv_path, ["-e", "."])
            yield


@contextmanager
def modify_environment_variable(name: str, value: str) -> Iterator[None]:
    original_value = os.environ.get(name)
    os.environ[name] = value
    yield
    if original_value is not None:
        os.environ[name] = original_value
    else:
        del os.environ[name]


@contextmanager
def clear_module_from_cache(module_name: str) -> Iterator[None]:
    matches = {key for key in sys.modules if key.startswith(module_name)}
    for match in matches:
        del sys.modules[match]
    yield
    matches = {key for key in sys.modules if key.startswith(module_name)}
    for match in matches:
        del sys.modules[match]


@contextmanager
def set_env_var(name: str, value: str) -> Iterator[None]:
    original_value = os.environ.get(name)
    os.environ[name] = value
    yield
    if original_value is not None:
        os.environ[name] = original_value
    else:
        del os.environ[name]


def convert_pyproject_toml_to_dg_toml(pyproject_toml_path: Path, dg_toml_path: Path) -> None:
    """Convert a pyproject.toml file to a dg.toml file."""
    pyproject_toml = tomlkit.parse(pyproject_toml_path.read_text())
    dg_toml_path.write_text(
        tomlkit.dumps(get_toml_node(pyproject_toml, ("tool", "dg"), tomlkit.items.Table))
    )
    delete_toml_node(pyproject_toml, ("tool", "dg"))

    # Delete the pyproject.toml file if it is empty after removing the dg section
    if (
        len(pyproject_toml) == 1
        and len(get_toml_node(pyproject_toml, ("tool",), tomlkit.items.Table)) == 0
    ):
        pyproject_toml_path.unlink()
    else:
        pyproject_toml_path.write_text(tomlkit.dumps(pyproject_toml))


def convert_dg_toml_to_pyproject_toml(dg_toml_path: Path, pyproject_toml_path: Path) -> None:
    """Convert a dg.toml file to a pyproject.toml file."""
    dg_toml = tomlkit.parse(dg_toml_path.read_text()).unwrap()
    if not pyproject_toml_path.exists():
        pyproject_toml_path.write_text(tomlkit.dumps({}))
    with modify_toml(pyproject_toml_path) as pyproject_toml:
        assert not has_toml_node(
            pyproject_toml, ("tool", "dg")
        ), "pyproject.toml already has a tool.dg section"
        if not has_toml_node(pyproject_toml, ("tool",)):
            set_toml_node(pyproject_toml, ("tool",), tomlkit.table())
        set_toml_node(pyproject_toml, ("tool", "dg"), dg_toml)
    dg_toml_path.unlink()


# ########################
# ##### TERMINAL OUTPUT UTILS
# ########################

STANDARDIZE_BOX_CHARACTERS_MAP = str.maketrans(
    {
        # Curved box characters mapped to straight
        "\u256d": "\u250c",  # ╭ -> ┌
        "\u256e": "\u2510",  # ╮ -> ┐
        "\u256f": "\u2518",  # ╯ -> ┘
        "\u2570": "\u2514",  # ╰ -> └
        # Thickr box characters mappend to thin
        "\u250f": "\u250c",  # ┏ -> ┌
        "\u2513": "\u2510",  # ┓ -> ┐
        "\u2517": "\u2514",  # ┗ -> └
        "\u251b": "\u2518",  # ┛ -> ┘
        "\u2503": "\u2502",  # ┃ -> │
        "\u2501": "\u2500",  # ━ -> ─
        "\u2523": "\u251c",  # ┣ -> ├
        "\u2533": "\u252c",  # ┳ -> ┬
        "\u253b": "\u2534",  # ┻ -> ┴
        "\u254b": "\u253c",  # ╋ -> ┼
        "\u252b": "\u2524",  # ┫ -> ┤
        "\u2521": "\u251c",  # ┡ -> ├
        "\u2547": "\u253c",  # ╇ -> ┼
        "\u2529": "\u2524",  # ┩ -> ┤
        # Double-lined box characters mapped to thin
        "\u2550": "\u2500",  # ═ -> ─
        "\u2551": "\u2502",  # ║ -> │
        "\u2554": "\u250c",  # ╔ -> ┌
        "\u2557": "\u2510",  # ╗ -> ┐
        "\u255a": "\u2514",  # ╚ -> └
        "\u255d": "\u2518",  # ╝ -> ┘
        "\u2560": "\u251c",  # ╠ -> ├
        "\u2563": "\u2524",  # ╣ -> ┤
        "\u2566": "\u252c",  # ╦ -> ┬
        "\u2569": "\u2534",  # ╩ -> ┴
        "\u256c": "\u253c",  # ╬ -> ┼
    }
)


# When testing commands that output tables/panels box characters, use this on both strings being
# compared. This is necessary because different platforms will sometimes output subtly different box
# characters.
def standardize_box_characters(text: str) -> str:
    return text.translate(STANDARDIZE_BOX_CHARACTERS_MAP)


@contextmanager
def fixed_panel_width(width: int = 80) -> Iterator[None]:
    # The width of panels in the help output is determined by the `COLUMNS` environment variable.
    # Unclear to me whether this controls the width of the terminal as a whole or just the width of
    # the panels rendered by `rich`, but regardless it is enough to achieve consistent output in the
    # below tests.
    #
    # On Windows, we set the width to width + 1 to get the same output as on Unix systems. This is
    # because when its the same width, the windows table comes out one character shorter. This may
    # be due to the use of two-character newlines (CRLF) on Windows vs one-character newline on
    # Unix. These are both whitespace and get stripped from output, but `rich` may be outputting one
    # character less of table width on Windows due to this.
    normalized_width = width + 1 if is_windows() else width
    with set_env_var("COLUMNS", str(normalized_width)):
        yield


# Typer's rich help output is difficult to match exactly, as it contains blank lines with extraneous
# whitespace. So we use this helper function to compare the output of the help message with the
# expected output. Comparing line-by-line also helps debugging.
#
# Also, windows tends to output different box drawing characters than Unix. Therefore we sub out any
# of the windows box drawing characters here for the Unix ones so that we can have standard test
# output.
def match_terminal_box_output(output: str, expected_output: str):
    standardized_output = standardize_box_characters(output)
    standardized_expected_output = standardize_box_characters(expected_output)
    standardized_output_lines = standardized_output.split("\n")
    standardized_expected_output_lines = standardized_expected_output.split("\n")
    for i in range(len(standardized_output_lines)):
        output_line = standardized_output_lines[i].strip()
        expected_output_line = standardized_expected_output_lines[i].strip()
        assert output_line == expected_output_line, (
            f"Line {i} of output does not match expected output.\n"
            f"Output  : {output_line}\n"
            f"Expected: {expected_output_line}"
        )
    return True


# Windows sometimes provides short (8.3) paths in output, which can be difficult to match exactly.
def normalize_windows_path(path: str) -> str:
    """Convert a Windows short (8.3) path to its long form.
    If the path does not exist or conversion fails, returns the original path.
    """
    import ctypes

    if sys.platform != "win32":
        raise RuntimeError("This function is only supported on Windows.")
    # Create a buffer for the result
    buffer_len = 260  # MAX_PATH typically 260 for Windows, though can be longer in practice
    buffer_ = ctypes.create_unicode_buffer(buffer_len)

    # Call GetLongPathNameW
    get_len = ctypes.windll.kernel32.GetLongPathNameW(path, buffer_, buffer_len)

    # If the buffer wasn't large enough, retry with bigger size
    if get_len > buffer_len:
        buffer_len = get_len
        buffer_ = ctypes.create_unicode_buffer(buffer_len)
        get_len = ctypes.windll.kernel32.GetLongPathNameW(path, buffer_, buffer_len)

    # get_len == 0 indicates error (e.g. file not found, path doesn't exist)
    if get_len == 0:
        return path

    return buffer_.value


# ########################
# ##### CLI RUNNER
# ########################


# NOTE: Pass use_fixed_test_components=True to use the dagster_test.components module instead of
# components loaded from entry points. This should be done whenever we want to test against a fixed
# set of known component types (as in inspect or list commands).
@dataclass
class ProxyRunner:
    original: CliRunner
    append_args: Optional[Sequence[str]] = None
    console_width: int = DG_CLI_MAX_OUTPUT_WIDTH

    @classmethod
    @contextmanager
    def test(
        cls,
        use_fixed_test_components: bool = False,
        verbose: bool = False,
        disable_cache: bool = False,
        console_width: int = DG_CLI_MAX_OUTPUT_WIDTH,
    ) -> Iterator[Self]:
        # We set the `COLUMNS` environment variable because this determines the width of output from
        # `rich`, which we use for generating tables etc.
        use_component_modules_args = (
            ["--use-component-module", STANDARD_TEST_COMPONENT_MODULE]
            if use_fixed_test_components
            else []
        )
        with TemporaryDirectory() as cache_dir, set_env_var("COLUMNS", str(console_width)):
            append_opts = [
                *use_component_modules_args,
                "--cache-dir",
                str(cache_dir),
                *(["--verbose"] if verbose else []),
                *(["--disable-cache"] if disable_cache else []),
            ]
            yield cls(CliRunner(), append_args=append_opts, console_width=console_width)

    def invoke(self, *args: str, **invoke_kwargs: Any) -> Result:
        # We need to find the right spot to inject global options. For the `dg scaffold`
        # command, we need to inject the global options before the final subcommand. For everything
        # else they can be appended at the end of the options.
        if args[0] == "scaffold":
            index = 1
        elif "--help" in args:
            index = args.index("--help")
        elif "--" in args:
            index = args.index("--")
        else:
            index = len(args)
        all_args = [*args[:index], *(self.append_args or []), *args[index:]]

        # For some reason the context setting `max_content_width` is not respected when using the
        # CliRunner, so we have to set it manually.
        result = self.original.invoke(
            dg_cli,
            all_args,
            terminal_width=self.console_width,
            **invoke_kwargs,
        )
        # Uncomment to get output from CLI invocations
        # print(str(result.stdout))
        return result

    @contextmanager
    def isolated_filesystem(self) -> Iterator[None]:
        with self.original.isolated_filesystem():
            yield


def assert_runner_result(result: Result, exit_0: bool = True) -> None:
    try:
        assert result.exit_code == 0 if exit_0 else result.exit_code != 0
    except AssertionError:
        if result.output:
            print(result.output)  # noqa: T201
        if result.exc_info:
            print_exception_info(result.exc_info)
        raise


def print_exception_info(
    exc_info: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    """Prints a nicely formatted traceback for the current exception."""
    exc_type, exc_value, exc_traceback = exc_info
    print("Exception Traceback (most recent call last):")  # noqa: T201
    formatted_traceback = "".join(traceback.format_tb(exc_traceback))
    print(formatted_traceback)  # noqa: T201
    print(f"{exc_type.__name__}: {exc_value}")  # noqa: T201


COMPONENT_INTEGRATION_TEST_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "dagster"
    / "dagster_tests"
    / "components_tests"
    / "integration_tests"
    / "integration_test_defs"
)


@contextlib.contextmanager
def create_project_from_components(
    runner: ProxyRunner, *src_paths: str, local_component_defn_to_inject: Optional[Path] = None
) -> Iterator[Path]:
    """Scaffolds a project with the given components in a temporary directory,
    injecting the provided local component defn into each component's __init__.py.
    """
    origin_paths = [COMPONENT_INTEGRATION_TEST_DIR / src_path for src_path in src_paths]
    with isolated_example_project_foo_bar(runner, component_dirs=origin_paths):
        for src_path in src_paths:
            components_dir = Path.cwd() / "src" / "foo_bar" / "defs" / src_path.split("/")[-1]
            if local_component_defn_to_inject:
                shutil.copy(local_component_defn_to_inject, components_dir / "__init__.py")

        yield Path.cwd()


def find_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@contextmanager
def modify_dg_toml_config_as_dict(path: Path) -> Iterator[dict[str, Any]]:
    """Modify a TOML file as a plain python dict, destroying comments and formatting.
    This will take account of the filename and yield only the dg config part. This is the root node
    for dg.toml files and the tool.dg section otherwise.
    """
    with modify_toml_as_dict(path) as toml_dict:
        if is_dg_specific_config_file(path):
            yield toml_dict
        elif not has_toml_node(toml_dict, ("tool", "dg")):
            raise KeyError(
                "TOML file does not have a tool.dg section. This is required for pyproject.toml files."
            )
        else:
            yield get_toml_node(toml_dict, ("tool", "dg"), dict)
