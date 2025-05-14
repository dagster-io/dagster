import inspect
import os
import re
import string
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Literal

from typing_extensions import TypeAlias

from dagster._utils import pushd
from dagster._utils.env import environ

MASK_TIME = (r"\d+:\d+(:?AM|PM)", "9:00AM")
MASK_SLING_WARNING = (r"warning.*\n", "")
MASK_SLING_PROMO = (r"Follow Sling.*\n", "")
MASK_SLING_DOWNLOAD_DUCKDB = (r".*downloading duckdb.*\n", "")
MASK_EDITABLE_DAGSTER = (r" --use-editable-dagster", "")
MASK_USING_ENVIRONMENT = (r"\nUsing[\s\S]*", "\n...")
MASK_TMP_WORKSPACE = (
    r"--workspace (/var/folders/.+|/tmp/.+)",
    "--workspace /tmp/workspace.yaml",
)
MASK_PLUGIN_CACHE_REBUILD = (r"Plugin object cache is invalidated or empty.*\n", "")
# Kind of a hack, "Running `uv sync` ..." appears after you enter "y" at the prompt, but when we
# simulate the input we don't get the "y" or newline we get in terminal so we slide it in here.
FIX_UV_SYNC_PROMPT = (r"Running `uv sync`\.\.\.", "y\nRunning `uv sync`...")


def make_project_path_mask(project_name: str):
    return (rf"\/.*?\/{project_name}", f"/.../{project_name}")


MASK_JAFFLE_PLATFORM = make_project_path_mask("jaffle-platform")

DAGSTER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "components"
    / "index"
)

EDITABLE_DIR = DAGSTER_ROOT / "python_modules" / "libraries"

DgTestPackageManager: TypeAlias = Literal["pip", "uv"]


SNIPPET_ENV = {
    # Controls width from click/rich
    "COLUMNS": "120",
    # No ansi escapes for color
    "NO_COLOR": "1",
    # Disable any activated virtualenv to prevent warning messages
    "VIRTUAL_ENV": "",
    "HOME": "/tmp",
    "DAGSTER_GIT_REPO_DIR": str(DAGSTER_ROOT),
    "UV_PYTHON": "3.12",
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


@contextmanager
def isolated_snippet_generation_environment() -> Iterator[Callable[[], int]]:
    snip_number = 0

    def get_next_snip_number():
        nonlocal snip_number
        snip_number += 1
        return snip_number

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
        yield get_next_snip_number


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
            EDITABLE_DIR / "dagster-dg",
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
            EDITABLE_DIR / "dagster-shared",
        ],
    )


def get_editable_install_cmd_for_paths(
    package_manager: DgTestPackageManager, paths: list[Path]
) -> str:
    if package_manager == "uv":
        lines = [
            "uv add --editable",
            *[(str(path)) for path in paths if path != Path(".")],
        ]
    elif package_manager == "pip":
        lines = [
            "pip install",
            *[f"--editable {path}" for path in paths],
        ]
    return " ".join(lines)
