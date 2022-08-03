from typing import List, Optional

from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL
from dagster_fivetran.utils import generate_materializations

from dagster import AssetKey, AssetOut, AssetsDefinition, Output
from dagster import _check as check
from dagster import multi_asset
from dagster._annotations import experimental


@experimental
def build_fivetran_assets(
    connector_id: str,
    destination_tables: List[str],
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: Optional[float] = None,
    io_manager_key: Optional[str] = None,
    asset_key_prefix: Optional[List[str]] = None,
) -> List[AssetsDefinition]:

    """
    Build a set of assets for a given Fivetran connector.

    Returns an AssetsDefintion which connects the specified ``asset_keys`` to the computation that
    will update them. Internally, executes a Fivetran sync for a given ``connector_id``, and
    polls until that sync completes, raising an error if it is unsuccessful. Requires the use of the
    :py:class:`~dagster_fivetran.fivetran_resource`, which allows it to communicate with the
    Fivetran API.

    Args:
        connector_id (str): The Fivetran Connector ID that this op will sync. You can retrieve this
            value from the "Setup" tab of a given connector in the Fivetran UI.
        destination_tables (List[str]): `schema_name.table_name` for each table that you want to be
            represented in the Dagster asset graph for this connection.
        poll_interval (float): The time (in seconds) that will be waited between successive polls.
        poll_timeout (Optional[float]): The maximum time that will waited before this operation is
            timed out. By default, this will never time out.
        io_manager_key (Optional[str]): The io_manager to be used to handle each of these assets.
        asset_key_prefix (Optional[List[str]]): A prefix for the asset keys inside this asset.
            If left blank, assets will have a key of `AssetKey([schema_name, table_name])`.

    Examples:

    .. code-block:: python

        from dagster import AssetKey, repository, with_resources

        from dagster_fivetran import fivetran_resource
        from dagster_fivetran.assets import build_fivetran_assets

        my_fivetran_resource = fivetran_resource.configured(
            {
                "api_key": {"env": "FIVETRAN_API_KEY"},
                "api_secret": {"env": "FIVETRAN_API_SECRET"},
            }
        )

        fivetran_assets = build_fivetran_assets(
            connector_id="foobar",
            table_names=["schema1.table1", "schema2.table2"],
        ])

        @repository
        def repo():
            return with_resources(
                fivetran_assets,
                resource_defs={"fivetran": my_fivetran_resource},
            )

    """

    asset_key_prefix = check.opt_list_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    tracked_asset_keys = {
        AssetKey(asset_key_prefix + table.split(".")) for table in destination_tables
    }

    @multi_asset(
        name=f"fivetran_sync_{connector_id}",
        outs={
            "_".join(key.path): AssetOut(io_manager_key=io_manager_key, key=key)
            for key in tracked_asset_keys
        },
        required_resource_keys={"fivetran"},
        compute_kind="fivetran",
    )
    def _assets(context):
        fivetran_output = context.resources.fivetran.sync_and_poll(
            connector_id=connector_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        for materialization in generate_materializations(
            fivetran_output, asset_key_prefix=asset_key_prefix
        ):
            # scan through all tables actually created, if it was expected then emit an Output.
            # otherwise, emit a runtime AssetMaterialization
            if materialization.asset_key in tracked_asset_keys:
                yield Output(
                    value=None,
                    output_name="_".join(materialization.asset_key.path),
                    metadata={
                        entry.label: entry.entry_data for entry in materialization.metadata_entries
                    },
                )
            else:
                yield materialization

    return [_assets]
