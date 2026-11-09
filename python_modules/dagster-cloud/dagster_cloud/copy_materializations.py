import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import AbstractSet, Annotated, Any  # noqa: UP035
from urllib.parse import urlparse

import requests
from dagster import AssetKey, AssetMaterialization
from dagster._core.definitions.partitions.utils.multi import MULTIPARTITION_KEY_DELIMITER
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord
from dagster._core.events import DagsterEvent, DagsterEventType, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID
from dagster._time import datetime_from_timestamp
from dagster_cloud_cli import ui
from dagster_cloud_cli.core.graphql_client import (
    create_agent_graphql_client,
    create_graphql_requests_session,
)
from typer import Option

from dagster_cloud.auth.constants import decode_agent_token
from dagster_cloud.storage.event_logs.storage import GraphQLEventLogStorage

SOURCE_ORG_TAG = "migration/source_org"
SOURCE_DEPLOYMENT_TAG = "migration/source_deployment"
SOURCE_RUN_ID_TAG = "migration/source_run_id"

EVENTS_PER_FETCH = 100

ASSET_NODES_QUERY = """
query CopyMaterializationsAssetNodes {
  assetNodes {
    assetKey {
      path
    }
    partitionDefinition {
      dimensionTypes {
        name
        type
        dynamicPartitionsDefinitionName
      }
    }
  }
}
"""

PARTITION_KEYS_QUERY = """
query CopyMaterializationsPartitionKeys($assetKeys: [AssetKeyInput!]) {
  assetNodes(assetKeys: $assetKeys) {
    partitionKeysByDimension {
      name
      partitionKeys
    }
  }
}
"""

# (name, type, dynamic definition name) per dimension, sorted by name; None if unpartitioned.
PartitionSignature = tuple[tuple[str, str, str | None], ...] | None


@dataclass
class AssetCopyPlan:
    asset_key: AssetKey
    events_to_write: list[EventLogEntry] = field(default_factory=list)
    already_in_target: int = 0
    missing_from_target: int = 0
    skip_reason: str | None = None


@dataclass(frozen=True)
class Endpoint:
    agent_token: str
    deployment: str
    org: str
    webserver_url: str
    agent_url: str


def resolve_endpoint(agent_token: str, deployment: str, url: str | None) -> Endpoint:
    """Resolve a deployment's URLs from its organization URL, or from the agent token."""
    if url is None:
        org, region = decode_agent_token(agent_token)
        if not org:
            raise ui.error(
                "Could not decode the organization from the agent token; pass its URL instead."
            )
        url = f"https://{org}.{region}.dagster.cloud" if region else f"https://{org}.dagster.cloud"
    parsed = urlparse(url)
    # The agent API lives on the organization's host with an `agent` label after the org name,
    # e.g. my-org.agent.dagster.cloud or my-org.agent.eu.dagster.cloud.
    org, _, domain = parsed.netloc.partition(".")
    return Endpoint(
        agent_token=agent_token,
        deployment=deployment,
        org=org,
        webserver_url=f"{parsed.scheme}://{parsed.netloc}",
        agent_url=f"{parsed.scheme}://{org}.agent.{domain}",
    )


def _create_event_log_storage(session, endpoint: Endpoint) -> GraphQLEventLogStorage:
    """Event log client for the deployment's agent API; makes no request."""
    client = create_agent_graphql_client(
        session,
        f"{endpoint.agent_url}/graphql",
        {"agent_token": endpoint.agent_token, "deployment": endpoint.deployment},
    )
    return GraphQLEventLogStorage(override_graphql_client=client)


def _query_webserver(
    endpoint: Endpoint, query: str, variables: Mapping[str, Any] | None = None
) -> Mapping[str, Any]:
    """Send a GraphQL query to the deployment's webserver and return its `data`."""
    response = requests.post(
        f"{endpoint.webserver_url}/{endpoint.deployment}/graphql",
        json={"query": query, "variables": variables if variables is not None else {}},
        headers={"Dagster-Cloud-Api-Token": endpoint.agent_token},
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise ui.error(f"Failed to query {endpoint.org}/{endpoint.deployment}: {body['errors']}")
    return body["data"]


def _fetch_partition_signatures(endpoint: Endpoint) -> dict[AssetKey, PartitionSignature]:
    """Fetch the partition signature of every asset defined in the deployment."""
    signatures: dict[AssetKey, PartitionSignature] = {}
    for node in _query_webserver(endpoint, ASSET_NODES_QUERY)["assetNodes"]:
        partitions_def = node["partitionDefinition"]
        signatures[AssetKey(node["assetKey"]["path"])] = (
            tuple(
                sorted(
                    (d["name"], d["type"], d["dynamicPartitionsDefinitionName"])
                    for d in partitions_def["dimensionTypes"]
                )
            )
            if partitions_def is not None
            else None
        )
    return signatures


def _fetch_target_partition_keys(endpoint: Endpoint, asset_key: AssetKey) -> list[set[str]]:
    """Fetch the asset's current partition keys, one set per dimension in dimension name order."""
    nodes = _query_webserver(
        endpoint, PARTITION_KEYS_QUERY, {"assetKeys": [{"path": asset_key.path}]}
    )["assetNodes"]
    if not nodes:
        return []
    dimensions = sorted(nodes[0]["partitionKeysByDimension"], key=lambda d: d["name"])
    return [set(d["partitionKeys"]) for d in dimensions]


def _is_target_partition(partition: str | None, partition_keys: Sequence[AbstractSet[str]]) -> bool:
    """Whether a partition exists in the target's keys; None only fits an unpartitioned asset."""
    if not partition_keys:
        return partition is None
    if partition is None:
        return False
    # Multi-partition keys join each dimension's key, in dimension name order.
    parts = (
        partition.split(MULTIPARTITION_KEY_DELIMITER) if len(partition_keys) > 1 else [partition]
    )
    return len(parts) == len(partition_keys) and all(
        part in keys for part, keys in zip(parts, partition_keys)
    )


def _fetch_events_by_storage_ids(
    storage: GraphQLEventLogStorage, asset_key: AssetKey, storage_ids: Sequence[int]
) -> list[EventLogRecord]:
    """Fetch materialization records by storage ID, `EVENTS_PER_FETCH` per request."""
    records = []
    for i in range(0, len(storage_ids), EVENTS_PER_FETCH):
        chunk = list(storage_ids[i : i + EVENTS_PER_FETCH])
        result = storage.fetch_materializations(
            AssetRecordsFilter(asset_key=asset_key, storage_ids=chunk), limit=len(chunk)
        )
        records.extend(result.records)
    return records


def _fetch_latest_source_records(
    storage: GraphQLEventLogStorage, asset_key: AssetKey
) -> list[EventLogRecord]:
    """Fetch the latest materialization per partition, or the latest overall if unpartitioned."""
    by_partition = storage.get_latest_storage_id_by_partition(
        asset_key, DagsterEventType.ASSET_MATERIALIZATION
    )
    if by_partition:
        return _fetch_events_by_storage_ids(storage, asset_key, sorted(by_partition.values()))
    return list(storage.fetch_materializations(asset_key, limit=1).records)


def build_copied_event(
    record: EventLogRecord, source_org: str, source_deployment: str
) -> EventLogEntry:
    """Build the runless event written to the target for a source materialization."""
    materialization = record.asset_materialization
    if materialization is None:
        raise ValueError(f"Record {record.storage_id} is not a materialization")

    tags = {
        **(materialization.tags if materialization.tags is not None else {}),
        SOURCE_ORG_TAG: source_org,
        SOURCE_DEPLOYMENT_TAG: source_deployment,
        SOURCE_RUN_ID_TAG: record.event_log_entry.run_id,
    }
    return EventLogEntry(
        user_message="",
        level=logging.INFO,
        job_name=RUNLESS_JOB_NAME,
        run_id=RUNLESS_RUN_ID,
        error_info=None,
        timestamp=record.timestamp,
        step_key=None,
        dagster_event=DagsterEvent(
            event_type_value=DagsterEventType.ASSET_MATERIALIZATION.value,
            job_name=RUNLESS_JOB_NAME,
            event_specific_data=StepMaterializationData(
                AssetMaterialization(
                    asset_key=materialization.asset_key,
                    description=materialization.description,
                    metadata=materialization.metadata,
                    partition=materialization.partition,
                    tags=tags,
                )
            ),
        ),
    )


def plan_asset_copy(
    asset_key: AssetKey,
    source: GraphQLEventLogStorage,
    target: GraphQLEventLogStorage,
    source_org: str,
    source_deployment: str,
    merge_partitions: bool,
    target_partition_keys: Sequence[AbstractSet[str]],
) -> AssetCopyPlan:
    """Read both deployments and decide which of the asset's source events to copy.

    - Skips the asset if the target's latest materialization is its own, unless merging.
    - Skips partitions missing from the target or already materialized there.
    """
    plan = AssetCopyPlan(asset_key=asset_key)
    records = _fetch_latest_source_records(source, asset_key)
    if not records:
        plan.skip_reason = "no materializations in source"
        return plan

    target_partitions = target.get_materialized_partitions(asset_key)
    target_latest = target.get_latest_materialization_events([asset_key]).get(asset_key)
    target_latest_materialization = (
        target_latest.asset_materialization if target_latest is not None else None
    )
    # Copied events are older but inserted later, so they would replace the target's own latest
    # materialization as the asset's "last materialized". A latest event tagged by an earlier
    # copy means a rerun can resume. Read from the full event: custom tags aren't indexed for
    # per-partition tag lookups.
    target_has_own_latest = target_latest_materialization is not None and (
        target_latest_materialization.tags is None
        or SOURCE_RUN_ID_TAG not in target_latest_materialization.tags
    )
    if target_has_own_latest and not merge_partitions:
        plan.skip_reason = "target already has its own materializations"
        return plan

    for record in sorted(records, key=lambda r: r.timestamp):
        partition = record.partition_key
        # e.g. dynamic keys the target hasn't added, or static keys it no longer defines.
        if not _is_target_partition(partition, target_partition_keys):
            plan.missing_from_target += 1
            continue
        if partition is None:
            if target_latest_materialization is not None:
                plan.already_in_target += 1
                continue
        elif partition in target_partitions:
            plan.already_in_target += 1
            continue
        plan.events_to_write.append(build_copied_event(record, source_org, source_deployment))
    return plan


def _format_ts(timestamp: float) -> str:
    return datetime_from_timestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")


def _print_plan(plan: AssetCopyPlan) -> None:
    key = plan.asset_key.to_user_string()
    if plan.skip_reason is not None:
        ui.print(f"  SKIP   {key}: {plan.skip_reason}")
        return
    skipped = (
        f"{plan.already_in_target} already in target,"
        f" {plan.missing_from_target} not in target partitions"
    )
    if not plan.events_to_write:
        ui.print(f"  NOOP   {key}: {skipped}")
        return
    first, last = plan.events_to_write[0].timestamp, plan.events_to_write[-1].timestamp
    ui.print(
        f"  WRITE  {key}: {len(plan.events_to_write)} events"
        f" ({_format_ts(first)} -> {_format_ts(last)}), {skipped}"
    )


def copy_materializations_command(
    source_deployment: Annotated[str, Option(help="Deployment to copy materializations from.")],
    target_deployment: Annotated[str, Option(help="Deployment to copy materializations into.")],
    source_agent_token: Annotated[
        str, Option(envvar="SOURCE_AGENT_TOKEN", help="Agent token for the source organization.")
    ],
    target_agent_token: Annotated[
        str, Option(envvar="TARGET_AGENT_TOKEN", help="Agent token for the target organization.")
    ],
    source_url: Annotated[
        str | None,
        Option(
            help="Source organization URL, e.g. https://my-org.dagster.cloud."
            " Defaults to the URL derived from the agent token."
        ),
    ] = None,
    target_url: Annotated[
        str | None,
        Option(
            help="Target organization URL, e.g. https://my-org.dagster.cloud."
            " Defaults to the URL derived from the agent token."
        ),
    ] = None,
    asset_key: Annotated[
        list[str] | None,
        Option(help="Slash-delimited asset key to copy. Repeatable. Defaults to all assets."),
    ] = None,
    merge_partitions: Annotated[
        bool,
        Option(help="Copy missing partitions even into assets the target already materialized."),
    ] = False,
    batch_size: Annotated[int, Option(help="Events written per request.")] = 50,
    dry_run: Annotated[
        bool,
        Option("--dry-run", help="Show what would be copied without writing anything."),
    ] = False,
):
    """Copy the latest asset materializations from one deployment into another.

    Copies the latest materialization per partition, keeping its timestamp, metadata and tags,
    as runless events tagged with their source organization, deployment and run.

    Only assets in the target's current asset graph with the same partitioning are copied, and
    only partitions that exist in the target; dynamic partition keys are not added. Assets outside
    that graph, such as ones removed from the code, are skipped. Partitions the target already has
    are skipped, as are assets the target materialized itself unless --merge-partitions is passed.

    Copied events are processed like new events in the target. Declarative Automation and
    sensors treat them as new materializations, so pause automation in the target deployment
    before confirming the copy. Asset health, freshness and table schema tracking also update,
    so alerts on those can fire. Copied events don't use credits or trigger materialization
    success or failure alerts, which are evaluated per run.

    Prints what will be copied and asks for confirmation before writing.
    """
    source_endpoint = resolve_endpoint(source_agent_token, source_deployment, source_url)
    target_endpoint = resolve_endpoint(target_agent_token, target_deployment, target_url)
    ui.print(
        f"{source_endpoint.org}/{source_deployment} -> {target_endpoint.org}/{target_deployment}"
    )

    with create_graphql_requests_session() as session:
        source = _create_event_log_storage(session, source_endpoint)
        target = _create_event_log_storage(session, target_endpoint)

        source_keys = (
            {AssetKey.from_user_string(k) for k in asset_key}
            if asset_key
            else set(source.all_asset_keys())
        )
        source_signatures = _fetch_partition_signatures(source_endpoint)
        target_signatures = _fetch_partition_signatures(target_endpoint)
        undefined_keys = source_keys - target_signatures.keys()
        for key in sorted(undefined_keys, key=lambda k: k.to_user_string()):
            ui.print(f"  SKIP   {key.to_user_string()}: not defined in target")

        plans = []
        for key in sorted(source_keys & target_signatures.keys(), key=lambda k: k.to_user_string()):
            target_signature = target_signatures[key]
            if key in source_signatures and source_signatures[key] != target_signature:
                plan = AssetCopyPlan(asset_key=key, skip_reason="partitioned differently in target")
            else:
                partition_keys = (
                    _fetch_target_partition_keys(target_endpoint, key)
                    if target_signature is not None
                    else []
                )
                plan = plan_asset_copy(
                    key,
                    source,
                    target,
                    source_endpoint.org,
                    source_deployment,
                    merge_partitions,
                    partition_keys,
                )
            _print_plan(plan)
            plans.append(plan)

        to_write = [plan for plan in plans if plan.events_to_write]
        total = sum(len(plan.events_to_write) for plan in to_write)
        ui.print(
            f"\n{total} events across {len(to_write)} assets;"
            f" {len(undefined_keys)} assets not defined in target;"
            f" {sum(1 for plan in plans if plan.skip_reason)} assets skipped."
        )
        if dry_run:
            ui.print("Dry run: nothing written.")
            return
        if total == 0:
            ui.print("Nothing to write.")
            return
        if not ui.confirm("Do you want to continue?", default=False):
            ui.print("Aborted: nothing written.")
            return

        # Within an asset, insertion order decides "latest", so each asset is written oldest first.
        written = 0
        for plan in to_write:
            for i in range(0, len(plan.events_to_write), batch_size):
                target.store_event_batch(plan.events_to_write[i : i + batch_size])
            written += len(plan.events_to_write)
            ui.print(
                f"  wrote {len(plan.events_to_write)} events for {plan.asset_key.to_user_string()}"
            )
        ui.print(f"Done: wrote {written} events.")
