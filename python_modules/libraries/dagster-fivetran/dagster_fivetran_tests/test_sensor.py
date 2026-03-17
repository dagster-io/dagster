from collections.abc import Iterator

import pytest
import responses
from dagster import AssetMaterialization, build_sensor_context
from dagster._core.test_utils import instance_for_test
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster_fivetran.resources import FIVETRAN_API_BASE, FIVETRAN_API_VERSION, FivetranWorkspace
from dagster_fivetran.sensor_builder import (
    FivetranPollingSensorCursor,
    build_fivetran_polling_sensor,
)

from dagster_fivetran_tests.conftest import (
    SAMPLE_CONNECTORS_FOR_GROUP,
    SAMPLE_DESTINATION_DETAILS,
    SAMPLE_GROUPS,
    SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR,
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_CONNECTOR_ID,
    TEST_CONNECTOR_NAME,
    TEST_DESTINATION_ID,
    TEST_GROUP_ID,
    TEST_MAX_TIME_STR,
    TEST_PREVIOUS_MAX_TIME_STR,
    get_fivetran_connector_api_url,
    get_sample_connection_details,
)


@pytest.fixture(name="fivetran_workspace")
def fivetran_workspace_fixture() -> FivetranWorkspace:
    return FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID,
        api_key=TEST_API_KEY,
        api_secret=TEST_API_SECRET,
    )


@pytest.fixture(name="sensor_api_mocks")
def sensor_api_mocks_fixture() -> Iterator[responses.RequestsMock]:
    """Base fixture that mocks the workspace data APIs and connector details for the sensor."""
    with (
        responses.RequestsMock() as rsps,
        instance_for_test(),
        scoped_definitions_load_context(),
    ):
        # Workspace data fetching mocks
        rsps.add(
            method=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/groups",
            json=SAMPLE_GROUPS,
            status=200,
        )
        rsps.add(
            method=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/groups/{TEST_GROUP_ID}/connectors",
            json=SAMPLE_CONNECTORS_FOR_GROUP,
            status=200,
        )
        rsps.add(
            method=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/destinations/{TEST_DESTINATION_ID}",
            json=SAMPLE_DESTINATION_DETAILS,
            status=200,
        )
        rsps.add(
            method=responses.GET,
            url=f"{get_fivetran_connector_api_url(TEST_CONNECTOR_ID)}/schemas",
            json=SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR,
            status=200,
        )
        yield rsps


def test_sensor_name(fivetran_workspace: FivetranWorkspace) -> None:
    """Verifies the default naming convention."""
    sensor_def = build_fivetran_polling_sensor(workspace=fivetran_workspace)
    assert sensor_def.name == f"fivetran_{TEST_ACCOUNT_ID}__sync_status_sensor"


def test_sensor_name_override(fivetran_workspace: FivetranWorkspace) -> None:
    """Verifies that the name parameter overrides the default."""
    sensor_def = build_fivetran_polling_sensor(
        workspace=fivetran_workspace, name="my_custom_sensor"
    )
    assert sensor_def.name == "my_custom_sensor"


def test_materializations_on_successful_sync(
    fivetran_workspace: FivetranWorkspace,
    sensor_api_mocks: responses.RequestsMock,
) -> None:
    """Connector with succeeded_at newer than cursor emits materializations for all enabled tables."""
    # Add connector details mock showing a successful sync
    sensor_api_mocks.add(
        method=responses.GET,
        url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
        json=get_sample_connection_details(
            succeeded_at=TEST_MAX_TIME_STR,
            failed_at=TEST_PREVIOUS_MAX_TIME_STR,
        ),
        status=200,
    )

    sensor_def = build_fivetran_polling_sensor(workspace=fivetran_workspace)

    # Run sensor with no cursor (first run)
    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        assert result.asset_events
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        # The sample schema has 2 schemas x 2 tables = 4 enabled tables
        assert len(mats) == 4

        # Verify metadata on materializations
        for mat in mats:
            assert mat.metadata
            assert "connector_url" in mat.metadata

        # Verify cursor was updated
        assert result.cursor
        cursor = deserialize_value(result.cursor, FivetranPollingSensorCursor)
        assert TEST_CONNECTOR_ID in cursor.effective_timestamp_by_connector_id


def test_no_materializations_when_no_new_sync(
    fivetran_workspace: FivetranWorkspace,
    sensor_api_mocks: responses.RequestsMock,
) -> None:
    """Cursor matches connector state so no events are emitted."""
    # Add two connector details mocks - one for first run, one for second run.
    # Workspace data is cached by FivetranWorkspace so only connector details are re-fetched.
    sensor_api_mocks.add(
        method=responses.GET,
        url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
        json=get_sample_connection_details(
            succeeded_at=TEST_MAX_TIME_STR,
            failed_at=TEST_PREVIOUS_MAX_TIME_STR,
        ),
        status=200,
    )
    sensor_api_mocks.add(
        method=responses.GET,
        url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
        json=get_sample_connection_details(
            succeeded_at=TEST_MAX_TIME_STR,
            failed_at=TEST_PREVIOUS_MAX_TIME_STR,
        ),
        status=200,
    )

    sensor_def = build_fivetran_polling_sensor(workspace=fivetran_workspace)

    # First run to populate cursor
    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance)
        first_result = sensor_def.evaluate_tick(context)
        assert first_result.cursor

        # Second run with same connector state
        context2 = build_sensor_context(instance=instance, cursor=first_result.cursor)
        second_result = sensor_def.evaluate_tick(context2)

        assert len(list(second_result.asset_events)) == 0


def test_failed_sync_advances_cursor(
    fivetran_workspace: FivetranWorkspace,
    sensor_api_mocks: responses.RequestsMock,
) -> None:
    """A failed sync (failed_at > succeeded_at > cursor) advances cursor but emits no materializations."""
    # Connector where failed_at is newer than succeeded_at
    sensor_api_mocks.add(
        method=responses.GET,
        url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
        json=get_sample_connection_details(
            succeeded_at=TEST_PREVIOUS_MAX_TIME_STR,
            failed_at=TEST_MAX_TIME_STR,
        ),
        status=200,
    )

    sensor_def = build_fivetran_polling_sensor(workspace=fivetran_workspace)

    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        # No materializations for failed sync
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 0

        # But cursor was still advanced
        assert result.cursor
        cursor = deserialize_value(result.cursor, FivetranPollingSensorCursor)
        assert TEST_CONNECTOR_ID in cursor.effective_timestamp_by_connector_id


def test_rescheduled_connector_warning(
    fivetran_workspace: FivetranWorkspace,
    sensor_api_mocks: responses.RequestsMock,
) -> None:
    """A rescheduled connector logs a warning and does not advance the cursor."""
    # Set up connector details where the connector was rescheduled to the future
    # and the sync hasn't completed yet (same timestamps as cursor)
    sensor_api_mocks.add(
        method=responses.GET,
        url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
        json=get_sample_connection_details(
            succeeded_at=TEST_PREVIOUS_MAX_TIME_STR,
            failed_at="0001-01-01T00:00:00.000000Z",
            rescheduled_for="2099-12-01T15:45:29.013729Z",
        ),
        status=200,
    )

    sensor_def = build_fivetran_polling_sensor(workspace=fivetran_workspace)

    # Set cursor to the current succeeded_at so there's no "new" sync
    from datetime import datetime

    prev_ts = datetime.fromisoformat(TEST_PREVIOUS_MAX_TIME_STR.replace("Z", "+00:00")).timestamp()
    initial_cursor = FivetranPollingSensorCursor(
        effective_timestamp_by_connector_id={TEST_CONNECTOR_ID: prev_ts}
    )

    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance, cursor=serialize_value(initial_cursor))
        result = sensor_def.evaluate_tick(context)

        # No materializations
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 0

        # Cursor should NOT have advanced - the timestamp stays the same
        assert result.cursor
        cursor = deserialize_value(result.cursor, FivetranPollingSensorCursor)
        assert cursor.effective_timestamp_by_connector_id[TEST_CONNECTOR_ID] == prev_ts


def test_cursor_serialization_roundtrip() -> None:
    """Verify that the cursor can be serialized and deserialized correctly."""
    cursor = FivetranPollingSensorCursor(
        effective_timestamp_by_connector_id={
            "connector_1": 1700000000.0,
            "connector_2": 1700000100.0,
        }
    )

    serialized = serialize_value(cursor)
    deserialized = deserialize_value(serialized, FivetranPollingSensorCursor)

    assert deserialized.effective_timestamp_by_connector_id == {
        "connector_1": 1700000000.0,
        "connector_2": 1700000100.0,
    }


def test_connector_selector_fn(
    fivetran_workspace: FivetranWorkspace,
    sensor_api_mocks: responses.RequestsMock,
) -> None:
    """Only selected connectors are polled."""
    # Selector that rejects all connectors - no connector details will be fetched
    sensor_def = build_fivetran_polling_sensor(
        workspace=fivetran_workspace,
        connector_selector_fn=lambda connector: connector.name == "nonexistent_connector",
    )

    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        # No materializations because connector was filtered out
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 0

    # Now test with a selector that accepts our connector.
    # Workspace data is cached, so only connector details mock is needed.
    sensor_api_mocks.add(
        method=responses.GET,
        url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
        json=get_sample_connection_details(
            succeeded_at=TEST_MAX_TIME_STR,
            failed_at=TEST_PREVIOUS_MAX_TIME_STR,
        ),
        status=200,
    )

    sensor_def_accepting = build_fivetran_polling_sensor(
        workspace=fivetran_workspace,
        connector_selector_fn=lambda connector: connector.name == TEST_CONNECTOR_NAME,
    )

    with instance_for_test() as instance:
        context = build_sensor_context(instance=instance)
        result = sensor_def_accepting.evaluate_tick(context)

        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 4
