import click


@click.group(name="project")
def project_cli() -> None:
    """(DEPRECATED) Use the `create-dagster` CLI instead."""
