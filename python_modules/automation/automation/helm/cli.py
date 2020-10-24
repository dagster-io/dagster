import os

import click
from automation.git import git_repo_root

from .schema.values import HelmValues

CLI_HELP = """Tools to help generate the schema file for the Dagster Helm chart.
"""


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option(
    "--command", type=click.Choice(["show", "apply"], case_sensitive=False), default="show"
)
def schema(command):
    """Generates the `values.schema.json` file according to user specified pydantic models.

    By default, the schema is printed on the console. If the schema is as expected, use
    `--command=apply` to save the changes on the existing `values.schema.json`.
    """
    schema_json = HelmValues.schema_json(indent=4)

    if command == "show":
        click.echo(schema_json, nl=False)
    elif command == "apply":
        values_schema_path = os.path.join(git_repo_root(), "helm/dagster/values.schema.json")
        with open(values_schema_path, "w") as f:
            f.write(schema_json)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
