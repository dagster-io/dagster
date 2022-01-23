import pytest
import responses
from dagster import AssetKey, DagsterStepOutputNotFoundError
from dagster.core.asset_defs import build_assets_job
from dagster_fivetran import fivetran_resource
from dagster_fivetran.assets import build_fivetran_assets
from dagster_fivetran.resources import FIVETRAN_API_BASE, FIVETRAN_CONNECTOR_PATH

from .utils import (
    DEFAULT_CONNECTOR_ID,
    get_sample_connector_response,
    get_sample_connector_schema_config,
    get_sample_sync_response,
    get_sample_update_response,
)


def test_fivetran_asset_keys():

    ft_asset = build_fivetran_assets(
        connector_id=DEFAULT_CONNECTOR_ID, asset_keys=[AssetKey("foo"), AssetKey("bar")]
    )
    assert ft_asset.asset_keys == {AssetKey("foo"), AssetKey("bar")}


@pytest.mark.parametrize(
    "asset_keys,should_error",
    [
        ([], False),
        ([AssetKey(["schema1", "tracked"])], False),
        ([AssetKey(["schema1", "tracked"]), AssetKey(["schema2", "tracked"])], False),
        ([AssetKey(["does", "notexist"])], True),
        ([AssetKey(["schema1", "tracked"]), AssetKey(["does", "notexist"])], True),
    ],
)
def test_fivetran_asset_run(asset_keys, should_error):

    ft_resource = fivetran_resource.configured({"api_key": "foo", "api_secret": "bar"})
    final_data = {"succeeded_at": "2021-01-01T02:00:00.0Z"}
    api_prefix = f"{FIVETRAN_API_BASE}/{FIVETRAN_CONNECTOR_PATH}{DEFAULT_CONNECTOR_ID}"

    fivetran_assets = build_fivetran_assets(
        name="my_cool_ft_assets",
        connector_id=DEFAULT_CONNECTOR_ID,
        asset_keys=asset_keys,
        poll_interval=0.1,
        poll_timeout=10,
    )

    # expect the multi asset to have one asset key and one output for each specified asset key
    assert fivetran_assets.asset_keys == set(asset_keys)
    assert len(fivetran_assets.op.output_defs) == len(asset_keys)

    fivetran_assets_job = build_assets_job(
        name="fivetran_assets_job",
        assets=[fivetran_assets],
        resource_defs={"fivetran": ft_resource},
    )

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
        rsps.add(rsps.POST, f"{api_prefix}/force", json=get_sample_sync_response())
        # connector schema
        rsps.add(
            rsps.GET,
            f"{api_prefix}/schemas",
            json=get_sample_connector_schema_config(
                tables=[
                    ("schema1", "tracked"),
                    ("schema1", "untracked"),
                    ("schema2", "tracked"),
                ]
            ),
        )
        # initial state
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # final state will be updated
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response(data=final_data))

        if should_error:
            with pytest.raises(DagsterStepOutputNotFoundError):
                fivetran_assets_job.execute_in_process()
        else:
            result = fivetran_assets_job.execute_in_process()
            assert result.success
            # make sure we only have outputs for the explicit asset keys
            outputs = [
                event
                for event in result.events_for_node("my_cool_ft_assets")
                if event.event_type_value == "STEP_OUTPUT"
            ]
            assert len(outputs) == len(asset_keys)

            # make sure we have asset materializations for all the schemas/tables that were actually sync'd
            asset_materializations = [
                event
                for event in result.events_for_node("my_cool_ft_assets")
                if event.event_type_value == "ASSET_MATERIALIZATION"
            ]
            assert len(asset_materializations) == 3
            found_asset_keys = set(
                mat.event_specific_data.materialization.asset_key for mat in asset_materializations
            )
            assert found_asset_keys == {
                AssetKey(["schema1", "tracked"]),
                AssetKey(["schema1", "untracked"]),
                AssetKey(["schema2", "tracked"]),
            }
