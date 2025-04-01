import pytest
import responses
from dagster import AssetKey, job, op
from dagster._core.test_utils import instance_for_test
from dagster_fivetran import FivetranOutput, fivetran_resource, fivetran_resync_op, fivetran_sync_op
from dagster_fivetran.resources import (
    FIVETRAN_API_BASE,
    FIVETRAN_API_VERSION_PATH,
    FIVETRAN_CONNECTOR_PATH,
)

from dagster_fivetran_tests.utils import (
    DEFAULT_CONNECTOR_ID,
    get_complex_sample_connector_schema_config,
    get_sample_connector_response,
    get_sample_resync_response,
    get_sample_sync_response,
    get_sample_update_response,
)


def test_fivetran_sync_op() -> None:
    ft_resource = fivetran_resource.configured({"api_key": "foo", "api_secret": "bar"})
    final_data = {"succeeded_at": "2021-01-01T02:00:00.0Z"}
    api_prefix = f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION_PATH}{FIVETRAN_CONNECTOR_PATH}{DEFAULT_CONNECTOR_ID}"

    @op
    def foo_op():
        pass

    @job(
        resource_defs={"fivetran": ft_resource},
        config={
            "ops": {
                "fivetran_sync_op": {
                    "config": {
                        "connector_id": DEFAULT_CONNECTOR_ID,
                        "poll_interval": 0.1,
                        "poll_timeout": 10,
                    }
                }
            }
        },
    )
    def fivetran_sync_job():
        fivetran_sync_op(start_after=foo_op())

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
        rsps.add(rsps.POST, f"{api_prefix}/force", json=get_sample_sync_response())
        # connector schema
        rsps.add(
            rsps.GET, f"{api_prefix}/schemas", json=get_complex_sample_connector_schema_config()
        )
        # initial state
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # n polls before updating
        for _ in range(2):
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # final state will be updated
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response(data=final_data))

        result = fivetran_sync_job.execute_in_process()
        assert result.output_for_node("fivetran_sync_op") == FivetranOutput(
            connector_details=get_sample_connector_response(data=final_data)["data"],  # pyright: ignore[reportArgumentType]
            schema_config=get_complex_sample_connector_schema_config()["data"],
        )
        asset_materializations = [
            event
            for event in result.events_for_node("fivetran_sync_op")
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(asset_materializations) == 3
        asset_keys = set(mat.materialization.asset_key for mat in asset_materializations)
        assert asset_keys == set(
            [
                AssetKey(["fivetran", "xyz1", "abc1"]),
                AssetKey(["fivetran", "xyz1", "abc2"]),
                AssetKey(["fivetran", "abc", "xyz"]),
            ]
        )


@pytest.mark.parametrize(
    "resync_params,endpoint,expected_assets",
    [
        (
            None,
            "/resync",
            [
                AssetKey(["fivetran", "xyz1", "abc1"]),
                AssetKey(["fivetran", "xyz1", "abc2"]),
                AssetKey(["fivetran", "abc", "xyz"]),
            ],
        ),
        (
            {"xyz1": ["abc1", "abc2"]},
            "/schemas/tables/resync",
            [AssetKey(["fivetran", "xyz1", "abc1"]), AssetKey(["fivetran", "xyz1", "abc2"])],
        ),
    ],
)
def test_fivetran_resync_op(resync_params, endpoint, expected_assets) -> None:
    ft_resource = fivetran_resource.configured({"api_key": "foo", "api_secret": "bar"})
    final_data = {"succeeded_at": "2021-01-01T02:00:00.0Z"}
    api_prefix = f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION_PATH}{FIVETRAN_CONNECTOR_PATH}{DEFAULT_CONNECTOR_ID}"

    @op
    def foo_op():
        pass

    @job(
        resource_defs={"fivetran": ft_resource},
        config={
            "ops": {
                "fivetran_resync_op": {
                    "config": {
                        "connector_id": DEFAULT_CONNECTOR_ID,
                        "resync_parameters": resync_params,
                        "poll_interval": 0.1,
                        "poll_timeout": 10,
                    }
                }
            }
        },
    )
    def fivetran_resync_job() -> None:
        fivetran_resync_op(start_after=foo_op())

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
        rsps.add(rsps.POST, api_prefix + endpoint, json=get_sample_resync_response())
        # connector schema
        rsps.add(
            rsps.GET, f"{api_prefix}/schemas", json=get_complex_sample_connector_schema_config()
        )
        # initial state
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # n polls before updating
        for _ in range(2):
            rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response())
        # final state will be updated
        rsps.add(rsps.GET, api_prefix, json=get_sample_connector_response(data=final_data))

        with instance_for_test() as instance:
            result = fivetran_resync_job.execute_in_process(instance=instance)
            assert result.output_for_node("fivetran_resync_op") == FivetranOutput(
                connector_details=get_sample_connector_response(data=final_data)["data"],  # pyright: ignore[reportArgumentType]
                schema_config=get_complex_sample_connector_schema_config()["data"],
            )
            asset_materializations = [
                event
                for event in result.events_for_node("fivetran_resync_op")
                if event.event_type_value == "ASSET_MATERIALIZATION"
            ]
            assert len(asset_materializations) == len(expected_assets)
            asset_keys = set(mat.materialization.asset_key for mat in asset_materializations)
            assert asset_keys == set(expected_assets)
