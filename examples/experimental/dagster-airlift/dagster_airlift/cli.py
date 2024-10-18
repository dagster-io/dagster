import click
from structlog import get_logger

logger = get_logger("dagster-airlift")


@click.group()
def cli():
    """Dagster Airlift CLI. Commands for interacting with the dagster-airlift package."""
    pass


@cli.group()
def proxy() -> None:
    """Commands for working with the Dagster-Airlift proxied state. Requires the `dagster-airlift[in-airflow]` package."""
    try:
        import dagster_airlift.in_airflow  # noqa
    except ImportError:
        raise Exception(
            "dagster-airlift[in-airflow] must be installed in the environment to use any `dagster-airlift proxy` commands."
        )


@proxy.command()
def scaffold():
    """Scaffolds a proxied state folder for the current Airflow installation. Goes in the Airflow Dags folder as <AIRFLOW_DAGS_FOLDER>/proxied_state.

    For each Dag, the proxied state will be filled out as False for all tasks, meaning execution behavior will not be proxied until the user changes the proxied state manually.
    """
    from dagster_airlift.in_airflow.scaffolding import scaffold_proxied_state

    scaffold_proxied_state(logger)


if __name__ == "__main__":
    cli()
