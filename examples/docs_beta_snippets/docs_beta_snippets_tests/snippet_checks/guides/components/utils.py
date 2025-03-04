import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from dagster._utils import pushd
from dagster._utils.env import environ

MASK_TIME = (r"\d+:\d+(:?AM|PM)", "9:00AM")
MASK_SLING_WARNING = (r"warning.*\n", "")
MASK_SLING_PROMO = (r"Follow Sling.*\n", "")
MASK_SLING_DOWNLOAD_DUCKDB = (r".*downloading duckdb.*\n", "")
MASK_EDITABLE_DAGSTER = (r" --use-editable-dagster", "")
MASK_JAFFLE_PLATFORM = (r"\/.*?\/jaffle-platform", "/.../jaffle-platform")

DAGSTER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "index"
)

EDITABLE_DIR = DAGSTER_ROOT / "python_modules" / "libraries"

SNIPPET_ENV = {
    # Controls width from click/rich
    "COLUMNS": "90",
    # No ansi escapes for color
    "NO_COLOR": "1",
    # Disable any activated virtualenv to prevent warning messages
    "VIRTUAL_ENV": "",
    "HOME": "/tmp",
    "DAGSTER_GIT_REPO_DIR": str(DAGSTER_ROOT),
}


@contextmanager
def isolated_snippet_generation_environment() -> Iterator[Callable[[], int]]:
    snip_number = 0

    def get_next_snip_number():
        nonlocal snip_number
        snip_number += 1
        return snip_number

    with TemporaryDirectory() as tempdir, pushd(tempdir), environ(SNIPPET_ENV):
        yield get_next_snip_number


def format_multiline(s: str) -> str:
    return textwrap.dedent(s).strip()
