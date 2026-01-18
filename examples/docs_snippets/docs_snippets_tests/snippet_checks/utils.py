import inspect
import logging
import os
import re
import shutil
import string
import subprocess
import textwrap
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Literal, Optional, TypeAlias, Union

import pexpect

from dagster._utils import pushd
from dagster._utils.env import environ

if TYPE_CHECKING:
    from selenium import webdriver

# https://stackoverflow.com/a/14693789
ANSI_ESCAPE = re.compile(
    r"""
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
""",
    re.VERBOSE,
)
DAGSTER_ROOT = Path(__file__).parent.parent.parent.parent.parent


def snippet_to_regex_fn(snippet: str) -> str:
    """Convert a snippet to a regex that matches the snippet, treating
    `...` as a wildcard.
    """
    return re.escape(snippet).replace(r"\.\.\.", ".*")


def re_ignore_before(match_str: str) -> tuple[str, str]:
    """Generates a regex substitution pair that replaces any text before `match_str` with
    an ellipses.
    """
    return (rf"[\s\S]*{re.escape(match_str)}", f"...\n{match_str}")


def re_ignore_after(match_str: str) -> tuple[str, str]:
    """Generates a regex substitution pair that replaces any text after `match_str` with
    an ellipses.
    """
    return (rf"{re.escape(match_str)}[\s\S]*", f"{match_str}\n...")


PWD_REGEX = re.compile(r"PWD=(.*?);")
USER_WARNING_REGEX = re.compile(r".*UserWarning.*")


def _run_command(
    cmd: Union[str, Sequence[str]],
    expect_error: bool = False,
    input_str: Optional[str] = None,
) -> str:
    if not isinstance(cmd, str):
        cmd = " ".join(cmd)

    try:
        if cmd.startswith("duckdb"):
            actual_output = _run_duckdb_command(cmd)
        else:
            actual_output = (
                subprocess.check_output(
                    f'{cmd.strip()} && echo "PWD=$(pwd);"',
                    shell=True,
                    # Default in CI is dash
                    executable="/bin/bash",
                    stderr=subprocess.STDOUT,
                    input=input_str.encode("utf-8") if input_str else None,
                )
                .decode("utf-8")
                .strip()
            )
        if expect_error:
            print(f"Ran command {cmd}")  # noqa: T201
            print("Got output:")  # noqa: T201
            print(actual_output)  # noqa: T201
            raise Exception("Expected command to fail")
    except subprocess.CalledProcessError as e:
        if expect_error:
            actual_output = e.output.decode("utf-8").strip()
        else:
            print(f"Ran command {cmd}")  # noqa: T201
            print("Got output:")  # noqa: T201
            print(e.output.decode("utf-8").strip())  # noqa: T201
            raise

    pwd = PWD_REGEX.search(actual_output)
    if pwd:
        actual_output = PWD_REGEX.sub("", actual_output)
        os.chdir(pwd.group(1))

    # Exclude user warnings from output, for example:
    # UserWarning: Found version mismatch between `dagster-shared` (1!0+dev) and `dagster-evidence` (0.1.4)
    user_warning = USER_WARNING_REGEX.search(actual_output)
    if user_warning:
        actual_output = USER_WARNING_REGEX.sub("", actual_output)

    actual_output = ANSI_ESCAPE.sub("", actual_output)

    return actual_output


# DuckDB modulates its output based on whether it is running in a terminal or not. In particular, it
# will only respect `.maxwidth` when running in a terminal, as of version 1.2. This means to
# standardize the output across environments (CI vs local dev on different machines), we need to
# mimic a terminal. We do this using `pexpect` to spawn a child process connected to a
# pseudo-terminal. This approach may also prove useful for other commands that modulate their output
# based on the terminal.
def _run_duckdb_command(cmd: str) -> str:
    pattern = r'(duckdb .*) -c "(.*)"'
    match = re.match(pattern, cmd)
    if not match:
        raise ValueError(f"Could not match pattern `{pattern}` in duckdb command {cmd}")

    duckdb_launch_cmd = match.group(1)
    sql_cmd = match.group(2)
    child = pexpect.spawn(duckdb_launch_cmd, encoding="utf-8")
    child.sendline(".maxwidth 110")
    child.sendline(sql_cmd)
    child.sendline(".quit")
    child.expect(pexpect.EOF)
    output = child.before
    assert output is not None
    output = ANSI_ESCAPE.sub("", output)
    # \r\r can sometimes happen due to weird interactions between pexpect and DuckDB
    output = output.replace("\r\r", "\r")
    return _extract_output_table_from_duckdb_output(output)


def _extract_output_table_from_duckdb_output(output: str) -> str:
    lines = output.splitlines()
    table_start_char = "┌"
    table_end_char = "└"
    start_idx = None
    end_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith(table_start_char):
            start_idx = idx
        if line.strip().startswith(table_end_char):
            end_idx = idx
            break
    assert start_idx is not None, "Could not find start of table"
    assert end_idx is not None, "Could not find end of table"
    return "\n".join(lines[start_idx : end_idx + 1])


def _assert_matches_or_update_snippet(
    contents: str,
    snippet_path: Path,
    update_snippets: bool,
    snippet_replace_regex: Optional[Sequence[tuple[str, str]]],
    custom_comparison_fn: Optional[Callable[[str, str], bool]],
):
    comparison_fn = custom_comparison_fn or (
        lambda actual, expected: actual == expected
    )
    if snippet_replace_regex:
        for regex, replacement in snippet_replace_regex:
            contents = re.sub(regex, replacement, contents, re.MULTILINE | re.DOTALL)

    snippet_output_file = Path(snippet_path)
    snippet_output_file.parent.mkdir(parents=True, exist_ok=True)

    if update_snippets:
        snippet_output_file.write_text(f"{contents.rstrip()}\n")
        print(f"Updated snippet at {snippet_path}")  # noqa: T201
    else:
        if not snippet_output_file.exists():
            raise Exception(f"Snippet at {snippet_path} does not exist")

        contents = contents.rstrip()
        snippet_contents = snippet_output_file.read_text().rstrip()
        if not comparison_fn(contents, snippet_contents):
            print(f"Snapshot mismatch {snippet_path}")  # noqa: T201
            print("\nActual file:")  # noqa: T201
            print(contents)  # noqa: T201
            print("\n\nExpected file:")  # noqa: T201
            print(snippet_contents)  # noqa: T201
        else:
            print(f"Snippet {snippet_path} passed")  # noqa: T201

        test_file_being_run = Path(inspect.stack()[2].filename)
        path_relative_to_docs = test_file_being_run.relative_to(
            DAGSTER_ROOT / "examples" / "docs_snippets"
        )
        assert comparison_fn(contents, snippet_contents), (
            "CLI snippets do not match. You may need to regenerate this snippet:"
            f"\n`cd $DAGSTER_GIT_REPO/examples/docs_snippets && tox -e docs_snapshot_update -- {path_relative_to_docs.as_posix()}`"
        )


def compare_tree_output(actual: str, expected: str) -> bool:
    """Custom command output comparison function for the output of calling
    `tree`. Often the order of the output is different on different platforms, so we
    just check that the filenames are identical rather than the precise tree order or
    structure.
    """
    TREE_PIPE_CHARS = ["│", "├", "└"]
    actual_non_filepath_lines = [
        line
        for line in actual.split("\n")
        if not any(line.strip().startswith(c) for c in TREE_PIPE_CHARS)
    ]
    expected_non_filepath_lines = [
        line
        for line in expected.split("\n")
        if not any(line.strip().startswith(c) for c in TREE_PIPE_CHARS)
    ]

    actual_filepath_lines = [
        line
        for line in actual.split("\n")
        if any(line.strip().startswith(c) for c in TREE_PIPE_CHARS)
    ]
    expected_filepath_lines = [
        line
        for line in expected.split("\n")
        if any(line.strip().startswith(c) for c in TREE_PIPE_CHARS)
    ]

    # strip out non-filename text from each of the filepath lines
    actual_filepath_lines = sorted(
        [line.strip().rsplit(" ", 1)[1] for line in actual_filepath_lines]
    )
    expected_filepath_lines = sorted(
        [line.strip().rsplit(" ", 1)[1] for line in expected_filepath_lines]
    )

    return (
        actual_non_filepath_lines == expected_non_filepath_lines
        and actual_filepath_lines == expected_filepath_lines
    )


SNIPPET_ENV = {
    # Controls width from click/rich
    "COLUMNS": "120",
    # No ansi escapes for color
    "NO_COLOR": "1",
    # Disable any activated virtualenv to prevent warning messages
    "VIRTUAL_ENV": "",
    "HOME": "/tmp",
    "DAGSTER_GIT_REPO_DIR": str(DAGSTER_ROOT),
    "UV_PYTHON": "3.11",
}


@contextmanager
def _get_snippet_working_dir() -> Iterator[str]:
    """If DAGSTER_CLI_SNIPPET_WORKING_DIR is set, use it as the working directory for all snippet tests.
    This makes it easier to debug the state of the working directory when a test fails.
    Otherwise, create a temporary directory and use that.
    """
    test_file_name = inspect.stack()[4].filename

    working_dir_from_env = os.getenv("DAGSTER_CLI_SNIPPET_WORKING_DIR")
    if working_dir_from_env:
        path = Path(working_dir_from_env) / Path(test_file_name).stem
        path.mkdir(parents=True, exist_ok=True)
        yield str(path)
    else:
        with TemporaryDirectory() as tempdir:
            yield (tempdir)


class SnippetGenerationContext:
    def __init__(
        self,
        snapshot_base_dir: Path,
        should_update_snippets: bool,
        global_snippet_replace_regexes: Sequence[tuple[str, str]],
    ) -> None:
        self._should_update_snippets = should_update_snippets
        self._snip_number = 0
        self._snapshot_base_dir = snapshot_base_dir
        self._global_snippet_replace_regexes = global_snippet_replace_regexes

    def get_next_snip_number(self) -> int:
        self._snip_number += 1
        return self._snip_number

    def run_command_and_snippet_output(
        self,
        cmd: Union[str, Sequence[str]],
        snippet_path: Optional[Union[Path, str]] = None,
        snippet_replace_regex: Optional[Sequence[tuple[str, str]]] = None,
        custom_comparison_fn: Optional[Callable[[str, str], bool]] = None,
        ignore_output: bool = False,
        expect_error: bool = False,
        print_cmd: Optional[str] = None,
        input_str: Optional[str] = None,
    ) -> str:
        """Run the given command and check that the output matches the contents of the snippet
        at `snippet_path`. If `update_snippets` is `True`, updates the snippet file with the
        output of the command.

        Args:
            cmd (Union[str, Sequence[str]): The command to run.
            snippet_path (Optional[Union[Path, str]]): Relative path to the snippet file to check/update.
            update_snippets (Optional[bool]): Whether to update the snippet file with the output.
            snippet_replace_regex (Optional[Sequence[tuple[str, str]]]): A list of regex
                substitution pairs to apply to the generated snippet file before checking it against the
                existing version. Note these will apply to both the command and the output of the
                command. Useful to remove dynamic content, e.g. the temporary directory path or
                timestamps.
            custom_comparison_fn (Optional[Callable]): A function that takes the output of the
                command and the snippet contents and returns whether they match. Useful for some
                commands (e.g. tree) where the output is frustratingly platform-dependent.
            ignore_output (bool): Whether to ignore the output of the command when updating the snippet.
                Useful when the output is too verbose or not meaningful.
        """
        output = _run_command(cmd, expect_error=expect_error, input_str=input_str)

        if snippet_path:
            print_cmd = print_cmd if print_cmd else str(cmd)

            if ignore_output:
                contents = print_cmd
            else:
                contents = f"{print_cmd}\n\n{output}"

            _assert_matches_or_update_snippet(
                contents=contents,
                snippet_path=self._snapshot_base_dir / snippet_path,
                update_snippets=self._should_update_snippets,
                snippet_replace_regex=[
                    *self._global_snippet_replace_regexes,
                    *(snippet_replace_regex or []),
                ],
                custom_comparison_fn=custom_comparison_fn,
            )
        return output

    def check_file(
        self,
        file_path: Union[Path, str],
        snippet_path: Optional[Union[Path, str]] = None,
        snippet_replace_regex: Optional[Sequence[tuple[str, str]]] = None,
    ):
        """Check that the contents of the file at `file_path` match the contents of the snippet
        at `snippet_path`. If `update_snippets` is `True`, updates the snippet file with the
        contents of the file.

        Used for steps where we want to show the user the contents of a file (e.g. one that's
        generated by the framework, or by output).

        Args:
            file_path (Union[Path, str]): The path to the file to check.
            snippet_path (Optional[Union[Path, str]]): Relative path to the snippet file to check/update.
            update_snippets (Optional[bool]): Whether to update the snippet file with the file contents.
            snippet_replace_regex (Optional[Sequence[tuple[str, str]]]): A list of regex
                substitution pairs to apply to the file contents before checking it against the snippet.
                Useful to remove dynamic content, e.g. the temporary directory path or timestamps.
        """
        file_path = Path(file_path)
        assert file_path.exists(), f"Expected file {file_path} to exist"
        contents = file_path.read_text()

        if snippet_path:
            _assert_matches_or_update_snippet(
                contents=contents,
                snippet_path=self._snapshot_base_dir / snippet_path,
                update_snippets=self._should_update_snippets,
                snippet_replace_regex=[
                    *self._global_snippet_replace_regexes,
                    *(snippet_replace_regex or []),
                ],
                custom_comparison_fn=None,
            )

    def create_file(
        self,
        file_path: Union[Path, str],
        contents: str,
        snippet_path: Optional[Union[Path, str]] = None,
        snippet_replace_regex: Optional[Sequence[tuple[str, str]]] = None,
    ):
        """Create a file with the given contents. If `snippet_path` is provided, outputs
        the contents to the snippet file too.

        Used for steps where the user is expected to create a file.

        Args:
            file_path (Union[Path, str]): The path to the file to create.
            contents (str): The contents to write to the file.
            snippet_path (Optional[Union[Path, str]]): Relative path to the snippet file to update.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(contents)
        if snippet_path:
            _assert_matches_or_update_snippet(
                contents=contents,
                snippet_path=self._snapshot_base_dir / snippet_path,
                update_snippets=True,
                snippet_replace_regex=[
                    *self._global_snippet_replace_regexes,
                    *(snippet_replace_regex or []),
                ],
                custom_comparison_fn=None,
            )


@contextmanager
def isolated_snippet_generation_environment(
    should_update_snippets: bool,
    snapshot_base_dir: Path,
    global_snippet_replace_regexes: Optional[Sequence[tuple[str, str]]] = None,
    clear_snapshot_dir_before_update: bool = True,
) -> Iterator[SnippetGenerationContext]:
    with (
        _get_snippet_working_dir() as tempdir,
        pushd(tempdir),
        TemporaryDirectory() as dg_cli_config_folder,
        TemporaryDirectory() as dagster_cloud_config_folder,
        environ(
            {
                **SNIPPET_ENV,
                "DG_CLI_CONFIG": str(Path(dg_cli_config_folder) / "dg.toml"),
                "DAGSTER_CLOUD_CLI_CONFIG": str(
                    Path(dagster_cloud_config_folder) / "config.yaml"
                ),
            }
        ),
    ):
        dg_config_path = Path(dg_cli_config_folder) / "dg.toml"
        dg_config_path.write_text(
            """
            [cli.telemetry]
            enabled = false
            """
        )
        if (
            should_update_snippets
            and snapshot_base_dir.exists()
            and clear_snapshot_dir_before_update
        ):
            shutil.rmtree(snapshot_base_dir)
            snapshot_base_dir.mkdir(parents=True, exist_ok=True)
        yield SnippetGenerationContext(
            snapshot_base_dir=snapshot_base_dir,
            should_update_snippets=should_update_snippets,
            global_snippet_replace_regexes=global_snippet_replace_regexes or [],
        )


def screenshot_page(
    get_webdriver: "Callable[[], webdriver.Chrome]",
    url: str,
    path: Path,
    update_screenshots: bool,
    width: Optional[int] = 1024,
    height: Optional[int] = 768,
) -> None:
    if not update_screenshots:
        return
    webdriver = get_webdriver()
    webdriver.set_window_size(width, height)
    webdriver.get(url)
    webdriver.save_screenshot(path)
