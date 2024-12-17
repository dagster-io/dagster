import re
from unittest.mock import MagicMock

import pytest
import responses
from dagster import AssetExecutionContext, AssetKey, Failure
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.materialize import materialize
from dagster._core.test_utils import environ
from dagster._vendored.dateutil import parser
from dagster_fivetran import FivetranOutput, FivetranWorkspace, fivetran_assets
from dagster_fivetran.translator import MIN_TIME_STR

from dagster_fivetran_tests.experimental.conftest import (
    SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR,
    SAMPLE_SUCCESS_MESSAGE,
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_MAX_TIME_STR,
    TEST_PREVIOUS_MAX_TIME_STR,
    TEST_SCHEMA_NAME,
    TEST_TABLE_NAME,
    get_fivetran_connector_api_url,
    get_sample_connection_details,
)


def test_basic_resource_request(
    connector_id: str,
    destination_id: str,
    group_id: str,
    all_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )
    client = resource.get_client()

    # fetch workspace data calls
    client.get_connectors_for_group(group_id=group_id)
    client.get_destination_details(destination_id=destination_id)
    client.get_groups()
    client.get_schema_config_for_connector(connector_id=connector_id)

    assert len(all_api_mocks.calls) == 4
    assert "Basic" in all_api_mocks.calls[0].request.headers["Authorization"]
    assert group_id in all_api_mocks.calls[0].request.url
    assert destination_id in all_api_mocks.calls[1].request.url
    assert "groups" in all_api_mocks.calls[2].request.url
    assert f"{connector_id}/schemas" in all_api_mocks.calls[3].request.url

    # connector details calls
    all_api_mocks.calls.reset()
    client.get_connector_details(connector_id=connector_id)
    client.update_schedule_type_for_connector(connector_id=connector_id, schedule_type="auto")

    assert len(all_api_mocks.calls) == 2
    assert connector_id in all_api_mocks.calls[0].request.url
    assert connector_id in all_api_mocks.calls[1].request.url
    assert all_api_mocks.calls[1].request.method == "PATCH"

    # columns config calls
    all_api_mocks.calls.reset()
    client.get_columns_config_for_table(
        connector_id=connector_id, schema_name=TEST_SCHEMA_NAME, table_name=TEST_TABLE_NAME
    )
    assert len(all_api_mocks.calls) == 1
    assert (
        f"{connector_id}/schemas/{TEST_SCHEMA_NAME}/tables/{TEST_TABLE_NAME}/columns"
        in all_api_mocks.calls[0].request.url
    )

    # sync calls
    all_api_mocks.calls.reset()
    client.start_sync(connector_id=connector_id)
    assert len(all_api_mocks.calls) == 3
    assert f"{connector_id}/force" in all_api_mocks.calls[2].request.url

    # resync calls
    all_api_mocks.calls.reset()
    client.start_resync(connector_id=connector_id, resync_parameters=None)
    assert len(all_api_mocks.calls) == 3
    assert f"{connector_id}/resync" in all_api_mocks.calls[2].request.url

    # resync calls with parameters
    all_api_mocks.calls.reset()
    client.start_resync(connector_id=connector_id, resync_parameters={"property1": ["string"]})
    assert len(all_api_mocks.calls) == 3
    assert f"{connector_id}/schemas/tables/resync" in all_api_mocks.calls[2].request.url

    # poll calls
    # Succeeded poll
    all_api_mocks.calls.reset()
    client.poll_sync(
        connector_id=connector_id,
        previous_sync_completed_at=parser.parse(MIN_TIME_STR),  # pyright: ignore[reportArgumentType]
    )
    assert len(all_api_mocks.calls) == 1

    # Timed out poll
    all_api_mocks.calls.reset()
    with pytest.raises(Failure, match=f"Sync for connector '{connector_id}' timed out"):
        client.poll_sync(
            connector_id=connector_id,
            # The poll process will time out because the value of
            # `FivetranConnector.last_sync_completed_at` does not change in the test
            previous_sync_completed_at=parser.parse(TEST_MAX_TIME_STR),  # pyright: ignore[reportArgumentType]
            poll_timeout=2,
            poll_interval=1,
        )

    # Failed poll
    all_api_mocks.calls.reset()
    # Replace the mock API call and set `failed_at` as more recent that `succeeded_at`
    all_api_mocks.replace(
        method_or_response=responses.GET,
        url=get_fivetran_connector_api_url(connector_id),
        json=get_sample_connection_details(
            succeeded_at=TEST_PREVIOUS_MAX_TIME_STR, failed_at=TEST_MAX_TIME_STR
        ),
        status=200,
    )
    with pytest.raises(Failure, match=f"Sync for connector '{connector_id}' failed!"):
        client.poll_sync(
            connector_id=connector_id,
            previous_sync_completed_at=parser.parse(MIN_TIME_STR),  # pyright: ignore[reportArgumentType]
            poll_timeout=2,
            poll_interval=1,
        )


@pytest.mark.parametrize(
    "method, n_polls, succeed_at_end",
    [
        ("sync_and_poll", 0, True),
        ("sync_and_poll", 0, False),
        ("sync_and_poll", 4, True),
        ("sync_and_poll", 4, False),
        ("sync_and_poll", 30, True),
        ("resync_and_poll", 0, True),
        ("resync_and_poll", 0, False),
        ("resync_and_poll", 4, True),
        ("resync_and_poll", 4, False),
        ("resync_and_poll", 30, True),
    ],
    ids=[
        "sync_short_success",
        "sync_short_failure",
        "sync_medium_success",
        "sync_medium_failure",
        "sync_long_success",
        "resync_short_success",
        "resync_short_failure",
        "resync_medium_success",
        "resync_medium_failure",
        "resync_long_success",
    ],
)
def test_sync_and_poll_client_methods(method, n_polls, succeed_at_end, connector_id):
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )
    client = resource.get_client()

    test_connector_api_url = get_fivetran_connector_api_url(connector_id)
    test_sync_api_url = (
        f"{test_connector_api_url}/force"
        if method == "sync_and_poll"
        else f"{test_connector_api_url}/resync"
    )

    test_succeeded_at = TEST_MAX_TIME_STR
    test_failed_at = TEST_PREVIOUS_MAX_TIME_STR
    # Set `failed_at` as more recent that `succeeded_at` if the sync and poll process is expected to fail
    if not succeed_at_end:
        test_succeeded_at = TEST_PREVIOUS_MAX_TIME_STR
        test_failed_at = TEST_MAX_TIME_STR

    # Create mock responses to mock full sync and poll behavior, used only in this test
    def _mock_interaction():
        with responses.RequestsMock() as response:
            response.add(
                responses.GET,
                f"{test_connector_api_url}/schemas",
                json=SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR,
            )
            response.add(responses.PATCH, test_connector_api_url, json=SAMPLE_SUCCESS_MESSAGE)
            response.add(responses.POST, test_sync_api_url, json=SAMPLE_SUCCESS_MESSAGE)
            # initial state
            response.add(
                responses.GET,
                test_connector_api_url,
                json=get_sample_connection_details(
                    succeeded_at=MIN_TIME_STR, failed_at=MIN_TIME_STR
                ),
            )
            # n polls before updating
            for _ in range(n_polls):
                response.add(
                    responses.GET,
                    test_connector_api_url,
                    json=get_sample_connection_details(
                        succeeded_at=MIN_TIME_STR, failed_at=MIN_TIME_STR
                    ),
                )
            # final state will be updated
            response.add(
                responses.GET,
                test_connector_api_url,
                json=get_sample_connection_details(
                    succeeded_at=test_succeeded_at, failed_at=test_failed_at
                ),
            )
            test_method = getattr(client, method)
            return test_method(connector_id, poll_interval=0.1)

    if succeed_at_end:
        assert _mock_interaction() == FivetranOutput(
            connector_details=get_sample_connection_details(
                succeeded_at=test_succeeded_at, failed_at=test_failed_at
            )["data"],
            schema_config=SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR["data"],
        )
    else:
        with pytest.raises(Failure, match="failed!"):
            _mock_interaction()


def test_fivetran_sync_and_poll_materialization_method(
    connector_id: str,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    sync_and_poll: MagicMock,
    capsys: pytest.CaptureFixture,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        @fivetran_assets(connector_id=connector_id, workspace=workspace, name=connector_id)
        def my_fivetran_assets(context: AssetExecutionContext, fivetran: FivetranWorkspace):
            yield from fivetran.sync_and_poll(context=context)

        # Mocked FivetranClient.sync_and_poll returns API response where all connector tables are expected
        result = materialize(
            [my_fivetran_assets],
            resources={"fivetran": workspace},
        )
        assert result.success
        asset_materializations = [
            event
            for event in result.events_for_node(connector_id)
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(asset_materializations) == 4
        materialized_asset_keys = {
            asset_materialization.asset_key for asset_materialization in asset_materializations
        }
        assert len(materialized_asset_keys) == 4
        assert my_fivetran_assets.keys == materialized_asset_keys

        # Mocked FivetranClient.sync_and_poll returns API response
        # where one expected table is missing and an unexpected table is present
        result = materialize(
            [my_fivetran_assets],
            resources={"fivetran": workspace},
        )

        assert result.success
        asset_materializations = [
            event
            for event in result.events_for_node(connector_id)
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(asset_materializations) == 4
        materialized_asset_keys = {
            asset_materialization.asset_key for asset_materialization in asset_materializations
        }
        assert len(materialized_asset_keys) == 4
        assert my_fivetran_assets.keys != materialized_asset_keys
        assert (
            AssetKey(["schema_name_in_destination_1", "another_table_name_in_destination_1"])
            in materialized_asset_keys
        )
        assert (
            AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"])
            not in materialized_asset_keys
        )

        captured = capsys.readouterr()
        assert re.search(
            r"dagster - WARNING - (?s:.)+ - An unexpected asset was materialized", captured.err
        )
        assert re.search(
            r"dagster - WARNING - (?s:.)+ - Assets were not materialized", captured.err
        )
