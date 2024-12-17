import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Iterator, Optional, Sequence, Tuple, Type, Union

from click.testing import CliRunner, Result
from dagster_dg.cli import cli as dg_cli
from dagster_dg.utils import discover_git_root, pushd


@contextmanager
def isolated_example_deployment_foo(runner: Union[CliRunner, "ProxyRunner"]) -> Iterator[None]:
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    with runner.isolated_filesystem():
        runner.invoke("generate", "deployment", "foo")
        with pushd("foo"):
            yield


@contextmanager
def isolated_example_code_location_bar(
    runner: Union[CliRunner, "ProxyRunner"], in_deployment: bool = True
) -> Iterator[None]:
    runner = ProxyRunner(runner) if isinstance(runner, CliRunner) else runner
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    if in_deployment:
        with isolated_example_deployment_foo(runner):
            runner.invoke(
                "generate",
                "code-location",
                "--use-editable-dagster",
                dagster_git_repo_dir,
                "bar",
            )
            with pushd("code_locations/bar"):
                yield
    else:
        with runner.isolated_filesystem():
            runner.invoke(
                "generate",
                "code-location",
                "--use-editable-dagster",
                dagster_git_repo_dir,
                "bar",
            )
            with pushd("bar"):
                yield


@dataclass
class ProxyRunner:
    original: CliRunner
    prepend_args: Optional[Sequence[str]] = None

    @classmethod
    def test(cls):
        return cls(CliRunner(), ["--builtin-component-lib", "dagster_components.test"])

    def invoke(self, *args: str):
        all_args = [*(self.prepend_args or []), *args]
        return self.original.invoke(dg_cli, all_args)

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
    exc_info: Tuple[Type[BaseException], BaseException, TracebackType],
) -> None:
    """Prints a nicely formatted traceback for the current exception."""
    exc_type, exc_value, exc_traceback = exc_info
    print("Exception Traceback (most recent call last):")  # noqa: T201
    formatted_traceback = "".join(traceback.format_tb(exc_traceback))
    print(formatted_traceback)  # noqa: T201
    print(f"{exc_type.__name__}: {exc_value}")  # noqa: T201
