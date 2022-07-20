# pylint: disable=print-call

from typing import List

import click
from dagster_format.tox import gather_toxfiles, sort_toxfile, transform_toxfile
from dagster_format.utils import discover_repo_root, in_cwd


@click.group(
    help="Tools for enforcing structural constraints throughout the Dagster repo.",
    context_settings={"max_content_width": 120},
)
def dagster_format():
    pass


@dagster_format.group
def tox():
    pass


@tox.command(
    help="Check if toxfiles are incorrectly formatted."
)
@click.argument("pattern", default=".*")
def check(pattern: str) -> None:
    """
    Run the toxfile formatter against all specified toxfiles (every toxfile in the repo if no
    pattern is provided) and list any files that would be changed. Exits with code 1 if any files
    would be changed. No files are actually written."
    """
    with in_cwd(discover_repo_root()):
        toxfiles = gather_toxfiles(pattern)
        failed: List[str] = []
        for tf in toxfiles:
            changed = transform_toxfile(tf, [sort_toxfile], audit=True)
            if changed:
                failed.append(tf)
        if len(failed) == 0:
            print(f"All {len(toxfiles)} toxfiles are formatted correctly.")
        else:
            print(
                f"Found {len(failed)} incorrectly formatted toxfiles. Run `dagster-format tox --all` to fix."
            )
            for tf in failed:
                print(f"  {tf}")


@tox.command(
    help="Format toxfiles in-place."
)
@click.argument("pattern", default=".*")
def format(pattern: str) -> None:  # pylint: disable=redefined-builtin
    """
    Run the toxfile formatter against all specified toxfiles (every toxfile in the repo if no
    pattern is provided). Overwrites and lists any file changed by the formatter."
    """
    with in_cwd(discover_repo_root()):
        toxfiles = gather_toxfiles(pattern)
        written: List[str] = []
        for tf in toxfiles:
            changed = transform_toxfile(tf, [sort_toxfile])
            if changed:
                written.append(tf)
        if len(written) == 0:
            print(f"None of {len(toxfiles)} toxfiles were changed.")
        else:
            print(f"Formatted {len(written)} incorrectly formatted toxfiles:")
            for tf in written:
                print(f"  {tf}")


def main():
    dagster_format()
