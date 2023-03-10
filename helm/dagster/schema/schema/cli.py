import os
import subprocess

import click

from .charts.dagster.values import DagsterHelmValues
from .charts.dagster_user_deployments.values import DagsterUserDeploymentsHelmValues


def git_repo_root():
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()


CLI_HELP = """Tools to help generate the schema file for the Dagster Helm chart.
"""


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.group()
def schema():
    """Generates the `values.schema.json` file according to user specified pydantic models."""


@schema.command()
def show():
    """Displays the json schema on the console."""
    click.echo("--- Dagster Helm Values ---")
    click.echo(DagsterHelmValues.schema_json(indent=4))

    click.echo("\n\n")
    click.echo("--- Dagster User Deployment Helm Values ---")
    click.echo(DagsterUserDeploymentsHelmValues.schema_json(indent=4))


@schema.command()
def apply():
    """Saves the json schema in the Helm `values.schema.json`."""
    helm_values_path_tuples = {
        (DagsterHelmValues, os.path.join(git_repo_root(), "helm", "dagster", "values.schema.json")),
        (
            DagsterUserDeploymentsHelmValues,
            os.path.join(
                git_repo_root(),
                "helm",
                "dagster",
                "charts",
                "dagster-user-deployments",
                "values.schema.json",
            ),
        ),
    }

    for helm_values, path in helm_values_path_tuples:
        with open(path, "w", encoding="utf8") as f:
            f.write(helm_values.schema_json(indent=4))
            f.write("\n")


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
