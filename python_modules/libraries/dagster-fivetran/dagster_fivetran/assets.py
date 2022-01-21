from typing import List, Optional

from dagster import AssetKey, Out, Output
from dagster.core.asset_defs import AssetsDefinition, multi_asset
from dagster.utils.backcompat import experimental
from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL
from dagster_fivetran.utils import generate_materializations


@experimental
def build_fivetran_assets(
    connector_id: str,
    asset_keys: List[AssetKey],
    name: Optional[str] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: Optional[float] = None,
    io_manager_key: Optional[str] = None,
) -> AssetsDefinition:

    """
    Create a @multi_asset for a given Fivetran connector.

    Returns an AssetsDefintion which connects the specified ``asset_keys`` to the computation that
    will update them. Internally, executes a Fivetran sync for a given ``connector_id``, and
    polls until that sync completes, raising an error if it is unsuccessful. Requires the use of the
    :py:class:`~dagster_fivetran.fivetran_resource`, which allows it to communicate with the
    Fivetran API.

    Args:
        connector_id (str): The Fivetran Connector ID that this op will sync. You can retrieve this
            value from the "Setup" tab of a given connector in the Fivetran UI.
        asset_keys (List[AssetKey]): The set of asset keys that Dagster will expect this asset to produce.
            These should be of the form ``AssetKey([<schema_name>, <table_name>])`` where
            ``<schema_name>`` and ``<table_name>`` represent the location of the tables in the
            Fivetran destination. Any AssetKey listed here MUST be sync'd every time this computation
            is executed, otherwise an exception will be raised. Additional tables that are updated
            during the sync but not listed here will be recorded with runtime AssetMaterialization
            events. The set of tables that are sync'd by Fivetran but are not explicitly set in the
            asset_keys argument may change over time as the Fivetran connector is updated.
        name (Optional[str]): A name for the underlying computation.
        poll_interval (float): The time (in seconds) that will be waited between successive polls.
        poll_timeout (Optional[float]): The maximum time that will waited before this operation is
            timed out. By default, this will never time out.
        io_manager_key (Optional[str]): The io_manager to be used to handle each of these assets.

    Examples:

    .. code-block:: python

        from dagster import AssetKey
        from dagster.core.asset_defs import build_assets_job

        from dagster_fivetran import fivetran_resource
        from dagster_fivetran.assets import build_fivetran_assets

        my_fivetran_resource = fivetran_resource.configured(
            {
                "api_key": {"env": "FIVETRAN_API_KEY"},
                "api_secret": {"env": "FIVETRAN_API_SECRET"},
            }
        )

        fivetran_assets = build_fivetran_assets(connector_id="foobar", asset_keys=[
            AssetKey(["schema1", "table1"]), AssetKey(["schema2", "table2"])
        ])

        my_fivetran_job = build_assets_job(
            "my_fivetran_job",
            assets=[fivetran_assets],
            resource_defs={"fivetran": my_fivetran_resource}
        )

    """

    @multi_asset(
        name=name or f"fivetran_sync_{connector_id}",
        outs={
            "_".join(key.path): Out(io_manager_key=io_manager_key, asset_key=key)
            for key in asset_keys
        },
        required_resource_keys={"fivetran"},
    )
    def _assets(context):
        fivetran_output = context.resources.fivetran.sync_and_poll(
            connector_id=connector_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        for materialization in generate_materializations(fivetran_output, asset_key_prefix=[]):
            # scan through all tables actually created, if it was expected then emit an Output.
            # otherwise, emit a runtime AssetMaterialization
            if materialization.asset_key in asset_keys:
                yield Output(
                    value=None,
                    output_name="_".join(materialization.asset_key.path),
                    metadata_entries=materialization.metadata_entries,
                )
            else:
                yield materialization

    return _assets
