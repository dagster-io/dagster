"""Tests for sensor deduplication of Dagster-triggered Fivetran syncs.

When both the polling sensor and the orchestration path (sync_and_poll) are active,
only one should emit materialization events for a given sync. The sensor checks the
instance's event log for existing materializations with matching sync_completed_at
metadata and skips duplicates.
"""

from datetime import datetime

import responses
from dagster import AssetKey, AssetMaterialization, build_sensor_context
from dagster._core.test_utils import instance_for_test
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster_fivetran.resources import FIVETRAN_API_BASE, FIVETRAN_API_VERSION, FivetranWorkspace
from dagster_fivetran.sensor_builder import (
    FivetranPollingSensorCursor,
    build_fivetran_polling_sensor,
)
from dagster_fivetran.translator import FivetranMetadataSet

from dagster_fivetran_tests.conftest import (
    SAMPLE_CONNECTORS_FOR_GROUP,
    SAMPLE_DESTINATION_DETAILS,
    SAMPLE_GROUPS,
    SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR,
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_CONNECTOR_ID,
    TEST_DESTINATION_ID,
    TEST_GROUP_ID,
    TEST_PREVIOUS_MAX_TIME_STR,
    get_fivetran_connector_api_url,
    get_sample_connection_details,
)

# Timestamps for the "new" sync that both paths might see
NEW_SYNC_TIME_STR = "2024-12-02T10:00:00.000000Z"
NEW_SYNC_TIMESTAMP = datetime.fromisoformat(NEW_SYNC_TIME_STR.replace("Z", "+00:00")).timestamp()

# Even newer sync for multi-sync scenarios
NEWER_SYNC_TIME_STR = "2024-12-02T12:00:00.000000Z"


def _build_workspace() -> FivetranWorkspace:
    return FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID,
        api_key=TEST_API_KEY,
        api_secret=TEST_API_SECRET,
    )


def _add_workspace_data_mocks(rsps: responses.RequestsMock) -> None:
    """Register the standard workspace data API mocks."""
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


def _simulate_orchestration_materializations(instance) -> None:
    """Simulate the orchestration path by writing materializations with sync_completed_at
    metadata into the instance's event log, as if sync_and_poll had already run.
    """
    # We need asset keys that match what the sensor would generate.
    # The sensor uses the default translator which creates keys like:
    #   AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"])
    # based on the SAMPLE_SCHEMA_CONFIG_FOR_CONNECTOR fixture (2 schemas x 2 tables = 4 tables).
    table_keys = [
        AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"]),
        AssetKey(["schema_name_in_destination_1", "table_name_in_destination_2"]),
        AssetKey(["schema_name_in_destination_2", "table_name_in_destination_1"]),
        AssetKey(["schema_name_in_destination_2", "table_name_in_destination_2"]),
    ]
    for key in table_keys:
        instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=key,
                metadata={
                    **FivetranMetadataSet(
                        connector_id=TEST_CONNECTOR_ID,
                        sync_completed_at=NEW_SYNC_TIMESTAMP,
                    ),
                },
            )
        )


def test_sensor_skips_sync_already_materialized_by_orchestration() -> None:
    """When the orchestration path has already materialized a sync, the sensor
    should detect the matching sync_completed_at and emit zero events,
    while still advancing the cursor.
    """
    workspace = _build_workspace()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        # Connector details show the new sync completed
        rsps.add(
            method=responses.GET,
            url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
            json=get_sample_connection_details(
                succeeded_at=NEW_SYNC_TIME_STR,
                failed_at=TEST_PREVIOUS_MAX_TIME_STR,
            ),
            status=200,
        )

        # Simulate orchestration having already written materializations
        _simulate_orchestration_materializations(instance)

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        # No duplicate materializations emitted
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 0

        # Cursor was still advanced so the sensor won't re-check this sync
        assert result.cursor
        cursor = deserialize_value(result.cursor, FivetranPollingSensorCursor)
        assert cursor.effective_timestamp_by_connector_id[TEST_CONNECTOR_ID] == NEW_SYNC_TIMESTAMP


def test_sensor_emits_when_no_prior_orchestration_materialization() -> None:
    """When there are no prior materializations in the instance (pure sensor mode),
    the sensor should emit events normally.
    """
    workspace = _build_workspace()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        rsps.add(
            method=responses.GET,
            url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
            json=get_sample_connection_details(
                succeeded_at=NEW_SYNC_TIME_STR,
                failed_at=TEST_PREVIOUS_MAX_TIME_STR,
            ),
            status=200,
        )

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        # Should emit 4 materializations (2 schemas x 2 tables)
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 4

        # All should have sync_completed_at metadata
        for mat in mats:
            metadata = FivetranMetadataSet.extract(mat.metadata)
            assert metadata.sync_completed_at == NEW_SYNC_TIMESTAMP


def test_sensor_emits_for_new_sync_after_orchestrated_sync() -> None:
    """If orchestration handled sync A, and then Fivetran runs sync B externally,
    the sensor should emit events for sync B (different sync_completed_at).
    """
    workspace = _build_workspace()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        # Simulate orchestration materialized sync A (NEW_SYNC_TIME_STR)
        _simulate_orchestration_materializations(instance)

        # But Fivetran has since run sync B (NEWER_SYNC_TIME_STR)
        rsps.add(
            method=responses.GET,
            url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
            json=get_sample_connection_details(
                succeeded_at=NEWER_SYNC_TIME_STR,
                failed_at=TEST_PREVIOUS_MAX_TIME_STR,
            ),
            status=200,
        )

        # Set cursor to sync A's timestamp (orchestration already handled it)
        prev_cursor = FivetranPollingSensorCursor(
            effective_timestamp_by_connector_id={TEST_CONNECTOR_ID: NEW_SYNC_TIMESTAMP}
        )

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)
        context = build_sensor_context(
            instance=instance,
            cursor=serialize_value(prev_cursor),
        )
        result = sensor_def.evaluate_tick(context)

        # Sensor should emit for sync B since it has a different timestamp
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 4

        newer_ts = datetime.fromisoformat(NEWER_SYNC_TIME_STR.replace("Z", "+00:00")).timestamp()
        for mat in mats:
            metadata = FivetranMetadataSet.extract(mat.metadata)
            assert metadata.sync_completed_at == newer_ts


def test_sensor_dedup_cursor_advances_even_when_skipping() -> None:
    """Verify that after dedup skips events, the next sensor tick with the same
    connector state produces no events (cursor was properly advanced).
    """
    workspace = _build_workspace()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        # Two connector detail responses: one per sensor tick
        for _ in range(2):
            rsps.add(
                method=responses.GET,
                url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
                json=get_sample_connection_details(
                    succeeded_at=NEW_SYNC_TIME_STR,
                    failed_at=TEST_PREVIOUS_MAX_TIME_STR,
                ),
                status=200,
            )

        _simulate_orchestration_materializations(instance)

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)

        # First tick: dedup skips, but cursor advances
        ctx1 = build_sensor_context(instance=instance)
        result1 = sensor_def.evaluate_tick(ctx1)
        assert len(list(result1.asset_events)) == 0
        assert result1.cursor

        # Second tick with advanced cursor: no new sync, no events, no extra API check for dedup
        ctx2 = build_sensor_context(instance=instance, cursor=result1.cursor)
        result2 = sensor_def.evaluate_tick(ctx2)
        assert len(list(result2.asset_events)) == 0


def test_sensor_dedup_with_stale_orchestration_materialization() -> None:
    """If the instance has materializations from an OLD orchestration sync,
    the sensor should still emit for a NEW sync (timestamps don't match).
    """
    workspace = _build_workspace()

    old_sync_time_str = "2024-11-01T10:00:00.000000Z"
    old_sync_timestamp = datetime.fromisoformat(
        old_sync_time_str.replace("Z", "+00:00")
    ).timestamp()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        # Write old materializations to instance
        instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"]),
                metadata={
                    **FivetranMetadataSet(
                        connector_id=TEST_CONNECTOR_ID,
                        sync_completed_at=old_sync_timestamp,
                    ),
                },
            )
        )

        # Connector shows a newer sync
        rsps.add(
            method=responses.GET,
            url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
            json=get_sample_connection_details(
                succeeded_at=NEW_SYNC_TIME_STR,
                failed_at=TEST_PREVIOUS_MAX_TIME_STR,
            ),
            status=200,
        )

        # Cursor is at the old sync time
        prev_cursor = FivetranPollingSensorCursor(
            effective_timestamp_by_connector_id={TEST_CONNECTOR_ID: old_sync_timestamp}
        )

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)
        context = build_sensor_context(
            instance=instance,
            cursor=serialize_value(prev_cursor),
        )
        result = sensor_def.evaluate_tick(context)

        # Should emit — the old materialization has a different sync_completed_at
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 4


def test_sensor_dedup_without_metadata_on_existing_materialization() -> None:
    """If existing materializations lack sync_completed_at metadata (legacy events),
    dedup should not match and the sensor should emit normally.
    """
    workspace = _build_workspace()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        # Write a materialization WITHOUT sync_completed_at (legacy/manual)
        instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=AssetKey(["schema_name_in_destination_1", "table_name_in_destination_1"]),
                metadata={
                    **FivetranMetadataSet(
                        connector_id=TEST_CONNECTOR_ID,
                        # No sync_completed_at — simulates legacy materialization
                    ),
                },
            )
        )

        rsps.add(
            method=responses.GET,
            url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
            json=get_sample_connection_details(
                succeeded_at=NEW_SYNC_TIME_STR,
                failed_at=TEST_PREVIOUS_MAX_TIME_STR,
            ),
            status=200,
        )

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        # Should emit — existing materialization has no sync_completed_at to match
        mats = [e for e in result.asset_events if isinstance(e, AssetMaterialization)]
        assert len(mats) == 4


def test_sensor_first_tick_with_orchestration_sets_cursor_correctly() -> None:
    """On the very first sensor tick (no cursor), if orchestration already materialized,
    cursor should advance past the orchestrated sync.
    """
    workspace = _build_workspace()

    with (
        responses.RequestsMock() as rsps,
        instance_for_test() as instance,
        scoped_definitions_load_context(),
    ):
        _add_workspace_data_mocks(rsps)

        rsps.add(
            method=responses.GET,
            url=get_fivetran_connector_api_url(TEST_CONNECTOR_ID),
            json=get_sample_connection_details(
                succeeded_at=NEW_SYNC_TIME_STR,
                failed_at=TEST_PREVIOUS_MAX_TIME_STR,
            ),
            status=200,
        )

        _simulate_orchestration_materializations(instance)

        sensor_def = build_fivetran_polling_sensor(workspace=workspace)
        # No cursor — first ever tick
        context = build_sensor_context(instance=instance)
        result = sensor_def.evaluate_tick(context)

        # No duplicates
        assert len(list(result.asset_events)) == 0

        # Cursor properly set
        assert result.cursor
        cursor = deserialize_value(result.cursor, FivetranPollingSensorCursor)
        assert cursor.effective_timestamp_by_connector_id[TEST_CONNECTOR_ID] == NEW_SYNC_TIMESTAMP
