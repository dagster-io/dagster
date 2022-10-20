import os
import sys
import tarfile
from io import BytesIO

import click
import requests

from .generate import _should_skip_file

# Currently we only download from 'master' branch
DEFAULT_GITHUB_URL = "https://codeload.github.com/dagster-io/dagster/tar.gz/master"
# Examples aren't that can't be downloaded from the dagster project CLI
EXAMPLES_TO_IGNORE = ["docs_snippets"]
# Hardcoded list of available examples. The list is tested against the examples folder in this mono
# repo to make sure it's up-to-date.
AVAILABLE_EXAMPLES = [
    "assets_dbt_python",
    "assets_modern_data_stack",
    "assets_pandas_pyspark",
    "assets_pandas_type_metadata",
    "assets_smoke_test",
    "tutorial_dbt_dagster",
    "deploy_docker",
    "deploy_ecs",
    "deploy_k8s",
    "development_to_production",
    "feature_graph_backed_assets",
    "project_fully_featured",
    "with_airflow",
    "with_great_expectations",
    "with_pyspark",
    "with_pyspark_emr",
]


def download_example_from_github(path: str, example: str):
    if example not in AVAILABLE_EXAMPLES:
        click.echo(
            click.style(
                f'Example "{example}" not available from the `dagster project` CLI. ', fg="red"
            )
            + "\nPlease specify the name of an official Dagster example. "
            + "You can find the available examples via `dagster project list-examples`."
        )
        sys.exit(1)

    path_to_new_project = os.path.normpath(path)
    path_to_selected_example = f"dagster-master/examples/{example}"

    click.echo(f"Downloading example '{example}'. This may take a while.")

    response = requests.get(DEFAULT_GITHUB_URL, stream=True)
    with tarfile.open(fileobj=BytesIO(response.raw.read()), mode="r:gz") as tar_file:
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

                with open(dest, "wb") as f:
                    f.write(fileobject.read())  # type: ignore
                fileobject.close()  # type: ignore
