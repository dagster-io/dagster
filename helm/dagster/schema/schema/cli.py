import os
from pathlib import Path

import click

from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.values import DagsterUserDeploymentsHelmValues

_DAGSTER_OSS_SUBDIRECTORY = "dagster-oss"


def _discover_oss_root(path: Path) -> Path:
    while path != path.parent:
        if (path / ".git").exists() or path.name == _DAGSTER_OSS_SUBDIRECTORY:
            return path
        path = path.parent
    raise ValueError("Could not find OSS root")


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
    oss_root = _discover_oss_root(Path(__file__))
    helm_values_path_tuples = {
        (DagsterHelmValues, os.path.join(oss_root, "helm", "dagster", "values.schema.json")),
        (
            DagsterUserDeploymentsHelmValues,
            os.path.join(
                oss_root,
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
