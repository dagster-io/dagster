import click


@click.group()
def cli():
    """Dagster Airlift CLI. Commands for interacting with the Dagster-Airlift package."""
    pass


@cli.group()
def proxy() -> None:
    """Commands for working with the Dagster-Airlift proxied state. Requires the `dagster-airlift[in-airflow]` package."""
    try:
        import dagster_airlift.in_airflow  # noqa
    except:
        raise Exception(
            "dagster-airlift[in-airflow] must be installed in the environment to use any `dagster-airlift proxy` commands."
        )


@proxy.command()
def scaffold():
    """Scaffolds a proxied state folder for the current Airflow installation. Goes in the airflow dags folder."""
    from dagster_airlift.in_airflow.scaffolding import scaffold_proxied_state

    scaffold_proxied_state()


if __name__ == "__main__":
    cli()
