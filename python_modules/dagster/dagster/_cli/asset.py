import click

from dagster._core.definitions.events import AssetKey
from dagster._core.instance import DagsterInstance


@click.group(name="asset")
def asset_cli():
    """
    Commands for working with Dagster assets.
    """


@asset_cli.command(name="wipe")
@click.argument("key", nargs=-1)
@click.option("--all", is_flag=True, help="Eliminate all asset key indexes")
@click.option("--noprompt", is_flag=True)
def asset_wipe_command(key, **cli_args):
    r"""
    Eliminate asset key indexes from event logs.

    Warning: Cannot be undone.

    \b
    Usage:
      dagster asset wipe --all
      dagster asset wipe <unstructured_asset_key_name>
      dagster asset wipe <json_string_of_structured_asset_key>
    """
    if not cli_args.get("all") and len(key) == 0:
        raise click.UsageError(
            "Error, you must specify an asset key or use `--all` to wipe all asset keys."
        )

    if cli_args.get("all") and len(key) > 0:
        raise click.UsageError("Error, cannot use more than one of: asset key, `--all`.")

    noprompt = cli_args.get("noprompt")

    with DagsterInstance.get() as instance:
        if len(key) > 0:
            asset_keys = [AssetKey.from_db_string(key_string) for key_string in key]
            prompt = (
                "Are you sure you want to remove the asset key indexes for these keys from the"
                " event logs? Type DELETE"
            )
        else:
            asset_keys = instance.all_asset_keys()
            prompt = (
                "Are you sure you want to remove all asset key indexes from the event logs? Type"
                " DELETE"
            )

        if noprompt:
            confirmation = "DELETE"
        else:
            confirmation = click.prompt(prompt)

        if confirmation == "DELETE":
            with DagsterInstance.get() as instance:
                instance.wipe_assets(asset_keys)
                click.echo("Removed asset indexes from event logs")
        else:
            click.echo("Exiting without removing asset indexes")
