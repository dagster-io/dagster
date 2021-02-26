import os
import subprocess

import click

from .values import HelmValues


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
    """
    Displays the json schema on the console.
    """
    schema_json = HelmValues.schema_json(indent=4)

    click.echo(schema_json)


@schema.command()
def apply():
    """
    Saves the json schema in the Helm `values.schema.json`.
    """
    schema_json = HelmValues.schema_json(indent=4)

    values_schema_path = os.path.join(git_repo_root(), "helm", "dagster", "values.schema.json")
    with open(values_schema_path, "w") as f:
        f.write(schema_json)
        f.write("\n")


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
