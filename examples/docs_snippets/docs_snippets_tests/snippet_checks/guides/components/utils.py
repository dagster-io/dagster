import inspect
import os
import re
import string
import textwrap
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, TypeAlias

from dagster._utils import pushd
from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.utils import DAGSTER_ROOT, SNIPPET_ENV

MASK_TIME = (r"\d+:\d+(:?AM|PM)", "9:00AM")
MASK_DBT_PARSE = (
    r"\nINFO:dagster.builtin:Running dbt command: `dbt parse --quiet`.\nINFO:dagster.builtin:Finished dbt command: `dbt parse --quiet`.\n",
    "",
)

MASK_SLING_WARNING = (r"warning.*\n", "")
MASK_SLING_PROMO = (r"Follow Sling.*\n", "")
MASK_SLING_DOWNLOAD_DUCKDB = (r".*downloading duckdb.*\n", "")
MASK_EDITABLE_DAGSTER = (r" --use-editable-dagster", "")
MASK_USING_ENVIRONMENT = (r"\nUsing[\s\S]*", "\n...")
MASK_TMP_WORKSPACE = (
    r"--workspace (/var/folders/.+|/tmp/.+)",
    "--workspace /tmp/workspace.yaml",
)
MASK_PLUGIN_CACHE_REBUILD = (r"Registry object cache is invalidated or empty.*\n", "")
# Kind of a hack, "Running `uv sync` ..." appears after you enter "y" at the prompt, but when we
# simulate the input we don't get the "y" or newline we get in terminal so we slide it in here.
FIX_UV_SYNC_PROMPT = (r"Running `uv sync`\.\.\.", "y\nRunning `uv sync`...")


def make_project_src_mask(project_name: str, project_name_underscored: str):
    return (
        rf"\/.*?\/{project_name}/src/{project_name_underscored}",
        f"/.../{project_name}/src/{project_name_underscored}",
    )


def make_project_scaffold_mask(project_name: str):
    return (rf"\/.*?\/{project_name}", f"/.../{project_name}")


MASK_JAFFLE_PLATFORM = make_project_src_mask("jaffle-platform", "jaffle_platform")

EDITABLE_DIR = DAGSTER_ROOT / "python_modules" / "libraries"
COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "index"
)


DgTestPackageManager: TypeAlias = Literal["pip", "uv"]


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


def make_letter_iterator() -> Callable[[], str]:
    letter_iter = (c for c in string.ascii_lowercase)

    def next_letter() -> str:
        return next(letter_iter)

    return next_letter


def format_multiline(s: str) -> str:
    return textwrap.dedent(s).strip()


def insert_before_matching_line(original: str, insert: str, pattern: str) -> str:
    """Insert `insert` string before the first line in `original` that matches `pattern`.

    Parameters:
    - original (str): The original multi-line string.
    - insert (str): The string to insert. Can contain newlines.
    - pattern (str): A regex pattern. If a line matches, insertion happens before that line.

    Returns:
    - str: The modified string with `insert` placed before the matched line.
    """
    output = []

    inserted = False
    for line in original.splitlines(keepends=True):
        if not inserted and re.search(pattern, line):
            output.append(insert if insert.endswith("\n") else insert + "\n")
            inserted = True
        output.append(line)

    if not inserted:
        raise ValueError("No matching line found for the given pattern.")

    return "".join(output)


def get_editable_install_cmd_for_dg(package_manager: DgTestPackageManager) -> str:
    return get_editable_install_cmd_for_paths(
        package_manager,
        [
            EDITABLE_DIR / "dagster-cloud-cli",
            EDITABLE_DIR / "dagster-dg-core",
            EDITABLE_DIR / "dagster-dg-cli",
            EDITABLE_DIR / "dagster-shared",
        ],
    )


def get_editable_install_cmd_for_project(
    project_path: Path, package_manager: DgTestPackageManager
) -> str:
    return get_editable_install_cmd_for_paths(
        package_manager,
        [
            project_path,
            EDITABLE_DIR.parent / "dagster",
            EDITABLE_DIR.parent / "dagster-pipes",
            EDITABLE_DIR.parent / "dagster-test",
            EDITABLE_DIR.parent / "dagster-webserver",
            EDITABLE_DIR.parent / "dagster-graphql",
            EDITABLE_DIR / "dagster-shared",
        ],
    )


def get_editable_install_cmd_for_paths(
    package_manager: DgTestPackageManager, paths: list[Path]
) -> str:
    if package_manager == "uv":
        lines = [
            "uv add --editable",
            *[str(path) for path in paths if path != Path(".")],
        ]
    elif package_manager == "pip":
        lines = [
            "pip install",
            *[f"--editable {path}" for path in paths],
        ]
    return " ".join(lines)
