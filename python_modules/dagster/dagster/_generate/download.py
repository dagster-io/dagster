import os
import sys
import tarfile
from io import BytesIO
from typing import IO, cast

import click
import requests

from .generate import _should_skip_file

# Currently we only download from 'master' branch
DEFAULT_GITHUB_URL = "https://codeload.github.com/dagster-io/dagster/tar.gz/master"
# Examples that can't be downloaded from the dagster project CLI
EXAMPLES_TO_IGNORE = ["docs_snippets"]


def download_example_from_github(path: str, example: str):
    if example in EXAMPLES_TO_IGNORE:
        click.echo(
            click.style(
                f'Example "{example}" not available from the `dagster project` CLI. ', fg="red"
            )
            + "\nPlease specify another official Dagster example. "
            + "You can find the examples in the Dagster repo: https://github.com/dagster-io/dagster/tree/master/examples"
        )
        sys.exit(1)

    path_to_new_project = os.path.normpath(path)
    path_to_selected_example = f"dagster-master/examples/{example}"

    click.echo(f"Downloading example '{example}'. This may take a while.")

    response = requests.get(DEFAULT_GITHUB_URL, stream=True)
    with tarfile.open(fileobj=BytesIO(response.raw.read()), mode="r:gz") as tar_file:
        try:
            tar_file.getmember(path_to_selected_example)
        except KeyError:
            click.echo(
                click.style(f'Can\'t find example "{example}". ', fg="red")
                + "\nPlease specify one of the official Dagster examples. "
                + "You can find the examples in the Dagster repo: https://github.com/dagster-io/dagster/tree/master/examples"
            )
            sys.exit(1)

        # Extract the selected example folder to destination
        subdir_and_files = [
            tarinfo
            for tarinfo in tar_file.getmembers()
            if tarinfo.name.startswith(path_to_selected_example)
        ]
        for member in subdir_and_files:
            if _should_skip_file(member.name):
                continue

            dest = member.name.replace(path_to_selected_example, path_to_new_project)

            if member.isdir():
                os.mkdir(dest)
            elif member.isreg():
                fileobject = tar_file.extractfile(member)
                cast(fileobject, IO[bytes])
                with open(dest, "wb") as f:
                    f.write(fileobject.read())
                fileobject.close()
