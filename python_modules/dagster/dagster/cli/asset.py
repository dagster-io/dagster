import click
from dagster.core.definitions.events import AssetKey
from dagster.core.instance import DagsterInstance


def create_asset_cli_group():
    group = click.Group(name="asset")
    group.add_command(asset_wipe_command)
    return group


@click.command(
    name="wipe",
    help=(
        "Eliminate asset key indexes from event logs. Warning: Cannot be undone\n\n"
        "Usage: \n\n"
        "  dagster asset wipe --all\n\n"
        "  dagster asset wipe <unstructured_asset_key_name>\n\n"
        "  dagster asset wipe <json_string_of_structured_asset_key>\n\n"
    ),
)
@click.argument("key", nargs=-1)
@click.option("--all", is_flag=True, help="Eliminate all asset key indexes")
def asset_wipe_command(key, **cli_args):
    if not cli_args.get("all") and len(key) == 0:
        raise click.UsageError(
            "Error, you must specify an asset key or use `--all` to wipe all asset keys."
        )

    if cli_args.get("all") and len(key) > 0:
        raise click.UsageError("Error, cannot use more than one of: asset key, `--all`.")

    with DagsterInstance.get() as instance:
        if not instance.is_asset_aware:
            raise click.UsageError(
                "Error, configured Dagster instance does not have asset aware event storage."
            )

        if len(key) > 0:
            asset_keys = [AssetKey.from_db_string(key_string) for key_string in key]
            prompt = (
                "Are you sure you want to remove the asset key indexes for these keys from the event "
                "logs? Type DELETE"
            )
        else:
            asset_keys = instance.all_asset_keys()
            prompt = "Are you sure you want to remove all asset key indexes from the event logs? Type DELETE"

        confirmation = click.prompt(prompt)
        if confirmation == "DELETE":
            with DagsterInstance.get() as instance:
                instance.wipe_assets(asset_keys)
                click.echo("Removed asset indexes from event logs")
        else:
            click.echo("Exiting without removing asset indexes")


asset_cli = create_asset_cli_group()
