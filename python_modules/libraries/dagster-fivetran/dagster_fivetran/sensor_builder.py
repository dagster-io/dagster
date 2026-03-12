from collections.abc import Sequence
from datetime import timedelta

from dagster import (
    AssetMaterialization,
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    sensor,
)
from dagster._annotations import public
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._record import as_dict, record
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import get_current_datetime
from dagster_shared.serdes import whitelist_for_serdes

from dagster_fivetran.resources import FivetranClient, FivetranWorkspace
from dagster_fivetran.translator import (
    ConnectorSelectorFn,
    DagsterFivetranTranslator,
    FivetranConnector,
    FivetranConnectorTableProps,
    FivetranMetadataSet,
    FivetranWorkspaceData,
)
from dagster_fivetran.utils import get_fivetran_connector_table_name, metadata_for_table

MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_FIVETRAN_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60


@whitelist_for_serdes
@record
class FivetranPollingSensorCursor:
    """A cursor that stores the last effective timestamp per connector."""

    effective_timestamp_by_connector_id: dict[str, float] = {}


@record
class ConnectorSyncResult:
    connector_id: str
    new_completed_at: float | None
    asset_events: Sequence[AssetMaterialization]


def _sync_already_materialized(
    context: SensorEvaluationContext,
    connector: FivetranConnector,
    workspace_data: FivetranWorkspaceData,
    translator: DagsterFivetranTranslator,
    sync_completed_at: float,
) -> bool:
    """Check if the given sync was already materialized by the orchestration path.

    Looks up the latest materialization for one representative asset of the connector
    and compares the sync_completed_at metadata. Returns True if the sync was already
    recorded, meaning the sensor should skip emitting duplicate events.
    """
    if not context.instance:
        return False

    schema_config = workspace_data.schema_configs_by_connector_id.get(connector.id)
    if not schema_config:
        return False

    # Pick the first enabled table as a representative probe for this connector
    asset_key = next(
        (
            translator.get_asset_spec(
                FivetranConnectorTableProps(
                    table=get_fivetran_connector_table_name(
                        schema_name=schema.name_in_destination,
                        table_name=table.name_in_destination,
                    ),
                    connector_id=connector.id,
                    connector_name=connector.name,
                    connector_url=connector.url,
                    destination_id=connector.destination_id,
                    schema_config=schema_config,
                    database=None,
                    service=None,
                )
            ).key
            for schema in schema_config.schemas.values()
            if schema.enabled
            for table in schema.tables.values()
            if table.enabled
        ),
        None,
    )
    if asset_key is None:
        return False

    latest_event = context.instance.get_latest_materialization_event(asset_key)
    if not latest_event or not latest_event.asset_materialization:
        return False

    existing_metadata = FivetranMetadataSet.extract(latest_event.asset_materialization.metadata)
    return existing_metadata.sync_completed_at == sync_completed_at


def check_connector_sync(
    context: SensorEvaluationContext,
    client: FivetranClient,
    connector: FivetranConnector,
    workspace_data: FivetranWorkspaceData,
    translator: DagsterFivetranTranslator,
    previous_completed_at: float | None,
) -> ConnectorSyncResult:
    """Check a single connector for new sync completions and return materializations."""
    connector_details = client.get_connector_details(connector.id)
    fresh_connector = FivetranConnector.from_connector_details(connector_details)

    current_completed_at = fresh_connector.last_sync_completed_at.timestamp()

    # No new sync since last check
    if previous_completed_at is not None and current_completed_at <= previous_completed_at:
        if fresh_connector.is_rescheduled:
            context.log.warning(
                f"Connector '{connector.id}' ({connector.name}) has been rescheduled by Fivetran "
                f"(rescheduled_for={fresh_connector.rescheduled_for}, "
                f"update_state={fresh_connector.update_state or ''}). "
                f"This is likely due to quota limits. The sensor will check again on the next tick."
            )
        return ConnectorSyncResult(
            connector_id=connector.id,
            new_completed_at=None,
            asset_events=[],
        )

    # New sync completed but it failed
    if not fresh_connector.is_last_sync_successful:
        context.log.warning(
            f"Connector '{connector.id}' ({connector.name}) completed a sync that failed "
            f"(failed_at={fresh_connector.failed_at}). Advancing cursor but not emitting materializations."
        )
        return ConnectorSyncResult(
            connector_id=connector.id,
            new_completed_at=current_completed_at,
            asset_events=[],
        )

    # New successful sync — check if the orchestration path already materialized this sync
    if _sync_already_materialized(
        context=context,
        connector=connector,
        workspace_data=workspace_data,
        translator=translator,
        sync_completed_at=current_completed_at,
    ):
        context.log.info(
            f"Connector '{connector.id}' ({connector.name}) sync at "
            f"{fresh_connector.succeeded_at} was already materialized by a Dagster-triggered run. "
            f"Advancing cursor but skipping duplicate materializations."
        )
        return ConnectorSyncResult(
            connector_id=connector.id,
            new_completed_at=current_completed_at,
            asset_events=[],
        )

    context.log.info(
        f"Connector '{connector.id}' ({connector.name}) completed a successful sync "
        f"(succeeded_at={fresh_connector.succeeded_at}). Generating materializations."
    )

    destination = workspace_data.destinations_by_id.get(fresh_connector.destination_id)
    schema_config = workspace_data.schema_configs_by_connector_id.get(connector.id)

    if not schema_config:
        context.log.warning(
            f"No schema config found for connector '{connector.id}'. Skipping materialization generation."
        )
        return ConnectorSyncResult(
            connector_id=connector.id,
            new_completed_at=current_completed_at,
            asset_events=[],
        )

    asset_events: list[AssetMaterialization] = []

    for schema in schema_config.schemas.values():
        if not schema.enabled:
            continue
        for table in schema.tables.values():
            if not table.enabled:
                continue

            table_name = get_fivetran_connector_table_name(
                schema_name=schema.name_in_destination,
                table_name=table.name_in_destination,
            )

            props = FivetranConnectorTableProps(
                table=table_name,
                connector_id=connector.id,
                connector_name=connector.name,
                connector_url=fresh_connector.url,
                destination_id=fresh_connector.destination_id,
                schema_config=schema_config,
                database=destination.database if destination else None,
                service=destination.service if destination else None,
                sync_frequency=fresh_connector.sync_frequency,
                schedule_type=fresh_connector.schedule_type,
                daily_sync_time=fresh_connector.daily_sync_time,
                connector_config=fresh_connector.config,
            )

            asset_spec = translator.get_asset_spec(props)

            metadata = metadata_for_table(
                as_dict(table),
                fresh_connector.url,
                database=destination.database if destination else None,
                schema=schema.name_in_destination,
                table=table.name_in_destination,
            )

            asset_events.append(
                AssetMaterialization(
                    asset_key=asset_spec.key,
                    description=(
                        f"Table generated via Fivetran sync: "
                        f"{schema.name_in_destination}.{table.name_in_destination}"
                    ),
                    metadata={
                        **metadata,
                        **FivetranMetadataSet(
                            connector_id=connector.id,
                            connector_name=connector.name,
                            destination_id=fresh_connector.destination_id,
                            destination_schema_name=schema.name_in_destination,
                            destination_table_name=table.name_in_destination,
                            sync_frequency_minutes=fresh_connector.sync_frequency,
                            schedule_type=fresh_connector.schedule_type,
                            daily_sync_time=fresh_connector.daily_sync_time,
                            sync_completed_at=current_completed_at,
                        ),
                    },
                )
            )

    return ConnectorSyncResult(
        connector_id=connector.id,
        new_completed_at=current_completed_at,
        asset_events=asset_events,
    )


@public
def build_fivetran_polling_sensor(
    *,
    workspace: FivetranWorkspace,
    dagster_fivetran_translator: DagsterFivetranTranslator | None = None,
    connector_selector_fn: ConnectorSelectorFn | None = None,
    minimum_interval_seconds: int = DEFAULT_FIVETRAN_SENSOR_INTERVAL_SECONDS,
    default_sensor_status: DefaultSensorStatus | None = None,
    name: str | None = None,
) -> SensorDefinition:
    """Creates a sensor that polls a Fivetran workspace for externally-triggered sync completions
    and emits AssetMaterialization events into Dagster's event log.

    This is useful when Fivetran connectors are run on Fivetran's auto-schedule (not triggered
    by Dagster) and you want Dagster to be aware of the resulting table updates.

    Args:
        workspace (FivetranWorkspace): The Fivetran workspace to poll.
        dagster_fivetran_translator (Optional[DagsterFivetranTranslator]): The translator to use
            to convert Fivetran content into AssetSpec. Defaults to DagsterFivetranTranslator.
        connector_selector_fn (Optional[ConnectorSelectorFn]): A function to filter which
            connectors are polled. If None, all connectors are polled.
        minimum_interval_seconds (int): The minimum interval in seconds between sensor runs.
            Defaults to 30.
        default_sensor_status (Optional[DefaultSensorStatus]): The default status of the sensor.
        name (Optional[str]): The name of the sensor. Defaults to
            ``fivetran_{account_id}__sync_status_sensor``.

    Returns:
        SensorDefinition: A sensor definition.
    """
    dagster_fivetran_translator = dagster_fivetran_translator or DagsterFivetranTranslator()
    sensor_name = name or f"fivetran_{workspace.account_id}__sync_status_sensor"

    @sensor(
        name=sensor_name,
        description=(f"Fivetran polling sensor for workspace account {workspace.account_id}"),
        minimum_interval_seconds=minimum_interval_seconds,
        default_status=default_sensor_status or DefaultSensorStatus.RUNNING,
    )
    def fivetran_sync_status_sensor(context: SensorEvaluationContext) -> SensorResult:
        """Sensor to report materialization events for Fivetran connector syncs."""
        context.log.info(f"Running Fivetran polling sensor for account {workspace.account_id}")

        try:
            cursor = (
                deserialize_value(context.cursor, FivetranPollingSensorCursor)
                if context.cursor
                else FivetranPollingSensorCursor()
            )
        except Exception as e:
            context.log.info(f"Failed to interpret cursor. Starting from scratch. Error: {e}")
            cursor = FivetranPollingSensorCursor()

        current_date = get_current_datetime()

        workspace_data = workspace.get_or_fetch_workspace_data()
        selected_workspace_data = workspace_data.to_workspace_data_selection(connector_selector_fn)

        client = workspace.get_client()

        all_asset_events: list[AssetMaterialization] = []
        new_effective_timestamps = dict(cursor.effective_timestamp_by_connector_id)

        for connector in selected_workspace_data.connectors_by_id.values():
            if get_current_datetime() - current_date > timedelta(seconds=MAIN_LOOP_TIMEOUT_SECONDS):
                context.log.info(
                    "Approaching sensor timeout. Will process remaining connectors on next tick."
                )
                break

            previous_completed_at = cursor.effective_timestamp_by_connector_id.get(connector.id)

            result = check_connector_sync(
                context=context,
                client=client,
                connector=connector,
                workspace_data=selected_workspace_data,
                translator=dagster_fivetran_translator,
                previous_completed_at=previous_completed_at,
            )

            all_asset_events.extend(result.asset_events)

            if result.new_completed_at is not None:
                new_effective_timestamps[connector.id] = result.new_completed_at

        new_cursor = FivetranPollingSensorCursor(
            effective_timestamp_by_connector_id=new_effective_timestamps,
        )
        context.update_cursor(serialize_value(new_cursor))

        context.log.info(
            f"Fivetran polling sensor complete. Emitting {len(all_asset_events)} materializations."
        )

        return SensorResult(asset_events=all_asset_events)

    return fivetran_sync_status_sensor
