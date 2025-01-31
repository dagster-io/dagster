import os
import shutil
import subprocess
import sys
import traceback
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Any, Optional, Union

import tomli
import tomli_w
from click.testing import CliRunner, Result
from dagster_dg.cli import (
    DG_CLI_MAX_OUTPUT_WIDTH,
    cli as dg_cli,
)
from dagster_dg.utils import discover_git_root, pushd
from typing_extensions import Self


@contextmanager
def isolated_components_venv(runner: Union[CliRunner, "ProxyRunner"]) -> Iterator[None]:
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    libraries_paths = [
        Path(dagster_git_repo_dir) / "python_modules" / name
        for name in ["dagster", "libraries/dagster-components", "dagster-pipes"]
    ]
    with runner.isolated_filesystem():
        subprocess.run(["uv", "venv", ".venv"], check=True)
        install_args: list[str] = []
        for path in libraries_paths:
            install_args.extend(["-e", str(path)])
        subprocess.run(
            ["uv", "pip", "install", "--python", ".venv/bin/python", *install_args], check=True
        )
        with modify_environment_variable("PATH", f"{Path.cwd()}/.venv/bin:{os.environ['PATH']}"):
            yield


@contextmanager
def isolated_example_deployment_foo(runner: Union[CliRunner, "ProxyRunner"]) -> Iterator[None]:
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    with runner.isolated_filesystem(), clear_module_from_cache("foo_bar"):
        runner.invoke("deployment", "scaffold", "foo")
        with pushd("foo"):
            yield


# Preferred example code location is foo-bar instead of a single word so that we can test the effect
# of hyphenation.
@contextmanager
def isolated_example_code_location_foo_bar(
    runner: Union[CliRunner, "ProxyRunner"],
    in_deployment: bool = True,
    skip_venv: bool = False,
    component_dirs: Sequence[Path] = [],
) -> Iterator[None]:
    """Scaffold a code location named foo_bar in an isolated filesystem.

    Args:
        runner: The runner to use for invoking commands.
        in_deployment: Whether the code location should be scaffolded inside a deployment directory.
        skip_venv: Whether to skip creating a virtual environment when scaffolding the code location.
        component_dirs: A list of component directories that will be copied into the code location component root.
    """
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    if in_deployment:
        fs_context = isolated_example_deployment_foo(runner)
        code_loc_path = "code_locations/foo-bar"
    else:
        fs_context = runner.isolated_filesystem()
        code_loc_path = "foo-bar"
    with fs_context:
        runner.invoke(
            "code-location",
            "scaffold",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            *(["--no-use-dg-managed-environment"] if skip_venv else []),
            "foo-bar",
        )
        with clear_module_from_cache("foo_bar"), pushd(code_loc_path):
            for src_dir in component_dirs:
                component_name = src_dir.name
                components_dir = Path.cwd() / "foo_bar" / "components" / component_name
                components_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_dir, components_dir, dirs_exist_ok=True)
            yield


@contextmanager
def isolated_example_component_library_foo_bar(
    runner: Union[CliRunner, "ProxyRunner"],
    lib_package_name: Optional[str] = None,
) -> Iterator[None]:
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with isolated_components_venv(runner):
        # We just use the code location generation function and then modify it to be a component library
        # only.
        runner.invoke(
            "code-location",
            "scaffold",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "--skip-venv",
            "foo-bar",
        )
        with clear_module_from_cache("foo_bar"), pushd("foo-bar"):
            shutil.rmtree("foo_bar/components")

            # Make it not a code location
            with modify_pyproject_toml() as pyproject_toml:
                pyproject_toml["tool"]["dg"]["is_code_location"] = False

                # We need to set any alternative lib package name _before_ we install into the
                # environment, since it affects entry points which are set at install time.
                if lib_package_name:
                    pyproject_toml["tool"]["dg"]["component_lib_package"] = lib_package_name
                    pyproject_toml["project"]["entry-points"]["dagster.components"]["foo_bar"] = (
                        lib_package_name
                    )
                    Path(*lib_package_name.split(".")).mkdir(exist_ok=True)

            # Install the component library into our venv
            subprocess.run(
                ["uv", "pip", "install", "--python", "../.venv/bin/python", "-e", "."], check=True
            )
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
    if module_name in sys.modules:
        del sys.modules[module_name]
    yield
    if module_name in sys.modules:
        del sys.modules[module_name]


@contextmanager
def set_env_var(name: str, value: str) -> Iterator[None]:
    original_value = os.environ.get(name)
    os.environ[name] = value
    yield
    if original_value is not None:
        os.environ[name] = original_value
    else:
        del os.environ[name]


@dataclass
class ProxyRunner:
    original: CliRunner
    append_args: Optional[Sequence[str]] = None
    console_width: int = DG_CLI_MAX_OUTPUT_WIDTH

    @classmethod
    @contextmanager
    def test(
        cls,
        use_test_component_lib: bool = True,
        verbose: bool = False,
        disable_cache: bool = False,
        console_width: int = DG_CLI_MAX_OUTPUT_WIDTH,
    ) -> Iterator[Self]:
        # We set the `COLUMNS` environment variable because this determines the width of output from
        # `rich`, which we use for generating tables etc.
        with TemporaryDirectory() as cache_dir, set_env_var("COLUMNS", str(console_width)):
            append_opts = [
                *(
                    ["--builtin-component-lib", "dagster_components.test"]
                    if use_test_component_lib
                    else []
                ),
                "--cache-dir",
                str(cache_dir),
                *(["--verbose"] if verbose else []),
                *(["--disable-cache"] if disable_cache else []),
            ]
            yield cls(CliRunner(), append_args=append_opts, console_width=console_width)

    def invoke(self, *args: str, **invoke_kwargs: Any) -> Result:
        # We need to find the right spot to inject global options. For the `dg component scaffold`
        # command, we need to inject the global options before the final subcommand. For everything
        # else they can be appended at the end of the options.
        if args[:2] == ("component", "scaffold"):
            index = 2
        elif "--help" in args:
            index = args.index("--help")
        elif "--" in args:
            index = args.index("--")
        else:
            index = len(args)
        all_args = [*args[:index], *(self.append_args or []), *args[index:]]

        # For some reason the context setting `max_content_width` is not respected when using the
        # CliRunner, so we have to set it manually.
        return self.original.invoke(
            dg_cli, all_args, terminal_width=self.console_width, **invoke_kwargs
        )

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


@contextmanager
def modify_pyproject_toml() -> Iterator[dict[str, Any]]:
    with open("pyproject.toml") as f:
        toml = tomli.loads(f.read())
    yield toml
    with open("pyproject.toml", "w") as f:
        f.write(tomli_w.dumps(toml))
