import logging
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import ExitStack
from dataclasses import dataclass, field
from typing import AbstractSet, Annotated, Any, Protocol  # noqa: UP035
from urllib.parse import urlparse

import requests
from dagster import AssetKey, AssetMaterialization
from dagster._core.definitions.partitions.utils.multi import MULTIPARTITION_KEY_DELIMITER
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord, EventRecordsResult
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
# Assets per request when reading latest materializations.
ASSET_CHUNK_SIZE = 100
# Smaller, since a single asset can have tens of thousands of partition keys.
PARTITION_KEYS_CHUNK_SIZE = 25
# Ursula rejects event batches larger than this.
MAX_EVENT_BATCH_SIZE = 50
DEFAULT_CONCURRENCY = 4
# Materializations aren't rate limited server side, so this protects the target's event log.
DEFAULT_MAX_EVENTS_PER_SECOND = 200.0


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
    assetKey {
      path
    }
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


class RateLimiter:
    """Spaces `acquire` calls across threads so units average at most `per_second`."""

    def __init__(
        self,
        per_second: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._per_second = per_second
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next_free = 0.0

    def acquire(self, units: int) -> None:
        with self._lock:
            now = self._clock()
            start = max(now, self._next_free)
            self._next_free = start + units / self._per_second
        if start > now:
            self._sleep(start - now)


class _Clients:
    """Source and target storages per thread, since a requests session isn't thread-safe."""

    def __init__(self, source_endpoint: Endpoint, target_endpoint: Endpoint, stack: ExitStack):
        self._source_ep = source_endpoint
        self._target_ep = target_endpoint
        self._stack = stack
        self._lock = threading.Lock()
        self._local = threading.local()

    def get(self) -> tuple[GraphQLEventLogStorage, GraphQLEventLogStorage]:
        storages = getattr(self._local, "storages", None)
        if storages is None:
            with self._lock:
                session = self._stack.enter_context(create_graphql_requests_session())
            storages = (
                _create_event_log_storage(session, self._source_ep),
                _create_event_log_storage(session, self._target_ep),
            )
            self._local.storages = storages
        return storages


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


def _fetch_target_partition_keys(
    endpoint: Endpoint, asset_keys: Sequence[AssetKey]
) -> dict[AssetKey, list[set[str]]]:
    """Fetch each asset's current partition keys, one set per dimension in dimension name order."""
    keys_by_asset: dict[AssetKey, list[set[str]]] = {}
    for i in range(0, len(asset_keys), PARTITION_KEYS_CHUNK_SIZE):
        chunk = asset_keys[i : i + PARTITION_KEYS_CHUNK_SIZE]
        nodes = _query_webserver(
            endpoint, PARTITION_KEYS_QUERY, {"assetKeys": [{"path": key.path} for key in chunk]}
        )["assetNodes"]
        for node in nodes:
            dimensions = sorted(node["partitionKeysByDimension"], key=lambda d: d["name"])
            keys_by_asset[AssetKey(node["assetKey"]["path"])] = [
                set(d["partitionKeys"]) for d in dimensions
            ]
    return keys_by_asset


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


class EventLogReader(Protocol):
    """The event log reads `plan_asset_copy` makes, served by a storage or `PrefetchedEventLog`."""

    def get_latest_storage_id_by_partition(
        self, asset_key: AssetKey, event_type: DagsterEventType
    ) -> Mapping[str, int]: ...

    def fetch_materializations(
        self, records_filter: AssetKey | AssetRecordsFilter, limit: int
    ) -> EventRecordsResult: ...

    def get_latest_materialization_events(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, EventLogEntry | None]: ...

    def get_materialized_partitions(self, asset_key: AssetKey) -> set[str]: ...


class PrefetchedEventLog:
    """Event log storage that serves latest-materialization reads from one batched request.

    - `get_latest_materialization_events` for the prefetched assets makes no request.
    - Every other read goes to the wrapped storage.
    """

    def __init__(self, storage: GraphQLEventLogStorage, asset_keys: Sequence[AssetKey]):
        self._storage = storage
        self._asset_keys = set(asset_keys)
        self._latest = storage.get_latest_materialization_events(asset_keys) if asset_keys else {}

    def get_latest_materialization_events(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, EventLogEntry | None]:
        if self._asset_keys.issuperset(asset_keys):
            return {key: self._latest[key] for key in asset_keys if key in self._latest}
        return self._storage.get_latest_materialization_events(asset_keys)

    def get_latest_storage_id_by_partition(
        self, asset_key: AssetKey, event_type: DagsterEventType
    ) -> Mapping[str, int]:
        return self._storage.get_latest_storage_id_by_partition(asset_key, event_type)

    def fetch_materializations(
        self, records_filter: AssetKey | AssetRecordsFilter, limit: int
    ) -> EventRecordsResult:
        return self._storage.fetch_materializations(records_filter, limit=limit)

    def get_materialized_partitions(self, asset_key: AssetKey) -> set[str]:
        return self._storage.get_materialized_partitions(asset_key)


def _fetch_events_by_storage_ids(
    storage: EventLogReader, asset_key: AssetKey, storage_ids: Sequence[int]
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


def build_copied_event(
    event: EventLogEntry, source_org: str, source_deployment: str
) -> EventLogEntry:
    """Build the runless event written to the target for a source materialization."""
    materialization = event.asset_materialization
    if materialization is None:
        raise ValueError(f"Event for run {event.run_id} is not a materialization")

    tags = {
        **(materialization.tags if materialization.tags is not None else {}),
        SOURCE_ORG_TAG: source_org,
        SOURCE_DEPLOYMENT_TAG: source_deployment,
        SOURCE_RUN_ID_TAG: event.run_id,
    }
    return EventLogEntry(
        user_message="",
        level=logging.INFO,
        job_name=RUNLESS_JOB_NAME,
        run_id=RUNLESS_RUN_ID,
        error_info=None,
        timestamp=event.timestamp,
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
    source: EventLogReader,
    target: EventLogReader,
    source_org: str,
    source_deployment: str,
    merge_partitions: bool,
    target_partition_keys: Sequence[AbstractSet[str]],
) -> AssetCopyPlan:
    """Read both deployments and decide which of the asset's source events to copy.

    - Skips the asset if the target's latest materialization is its own, unless merging.
    - Skips partitions missing from the target or already materialized there.
    - Fetches source events only for the partitions it copies.
    """
    plan = AssetCopyPlan(asset_key=asset_key)

    # 1. The source's materialized partitions, without fetching their events: storage IDs for a
    #    partitioned asset, the latest event for an unpartitioned one.
    storage_ids: Mapping[str, int] = {}
    latest_event = None
    if target_partition_keys:
        storage_ids = source.get_latest_storage_id_by_partition(
            asset_key, DagsterEventType.ASSET_MATERIALIZATION
        )
        source_partitions: list[str | None] = list(storage_ids)
    else:
        latest_event = source.get_latest_materialization_events([asset_key]).get(asset_key)
        materialization = latest_event.asset_materialization if latest_event is not None else None
        source_partitions = [materialization.partition] if materialization is not None else []
    if not source_partitions:
        plan.skip_reason = "no materializations in source"
        return plan

    # 2. Compare with the target.
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

    # No latest event means nothing materialized, so skip the request.
    target_partitions = (
        target.get_materialized_partitions(asset_key) if target_latest is not None else set()
    )
    to_copy = []
    for partition in source_partitions:
        # e.g. dynamic keys the target hasn't added, or static keys it no longer defines.
        if not _is_target_partition(partition, target_partition_keys):
            plan.missing_from_target += 1
        elif partition is None and target_latest_materialization is not None:
            plan.already_in_target += 1
        elif partition is not None and partition in target_partitions:
            plan.already_in_target += 1
        else:
            to_copy.append(partition)
    if not to_copy:
        return plan

    # 3. Fetch only the events of the partitions to copy.
    if storage_ids:
        storage_ids_to_copy = sorted(storage_ids[p] for p in to_copy if p is not None)
        events = [
            record.event_log_entry
            for record in _fetch_events_by_storage_ids(source, asset_key, storage_ids_to_copy)
        ]
    else:
        events = [latest_event] if latest_event is not None else []
    plan.events_to_write = [
        build_copied_event(event, source_org, source_deployment)
        for event in sorted(events, key=lambda e: e.timestamp)
    ]
    return plan


def _format_ts(timestamp: float) -> str:
    return datetime_from_timestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")


def _count(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


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
        f"  WRITE  {key}: {_count(len(plan.events_to_write), 'event')}"
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
    batch_size: Annotated[
        int,
        Option(min=1, max=MAX_EVENT_BATCH_SIZE, help="Events written per request."),
    ] = MAX_EVENT_BATCH_SIZE,
    concurrency: Annotated[
        int, Option(min=1, help="Assets read or written in parallel.")
    ] = DEFAULT_CONCURRENCY,
    max_events_per_second: Annotated[
        float,
        Option(min=1, help="Upper bound on events written per second, across all workers."),
    ] = DEFAULT_MAX_EVENTS_PER_SECOND,
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

    Copied events are processed like new events in the target. Sensors that read the event log,
    such as asset sensors, treat them as new materializations, so pause them in the target
    deployment before confirming the copy. Declarative Automation doesn't react to them, since
    their timestamps predate its latest evaluation. Asset health, freshness and table schema
    tracking also update, so alerts on those can fire. Copied events don't use credits or trigger materialization
    success or failure alerts, which are evaluated per run.

    Prints what will be copied and asks for confirmation before writing.
    """
    source_endpoint = resolve_endpoint(source_agent_token, source_deployment, source_url)
    target_endpoint = resolve_endpoint(target_agent_token, target_deployment, target_url)
    ui.print(
        f"{source_endpoint.org}/{source_deployment} -> {target_endpoint.org}/{target_deployment}"
    )

    with ExitStack() as stack:
        clients = _Clients(source_endpoint, target_endpoint, stack)
        source, _ = clients.get()

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

        def plan_chunk(chunk: Sequence[AssetKey]) -> list[AssetCopyPlan]:
            source, target = clients.get()
            comparable = [
                key
                for key in chunk
                if key not in source_signatures or source_signatures[key] == target_signatures[key]
            ]
            partitioned = [key for key in comparable if target_signatures[key] is not None]
            unpartitioned = [key for key in comparable if target_signatures[key] is None]

            # One request per side for the chunk's latest materializations, which
            # plan_asset_copy then reads without a request; its other reads stay per asset.
            chunk_source = PrefetchedEventLog(source, unpartitioned)
            chunk_target = PrefetchedEventLog(target, comparable)
            partition_keys = (
                _fetch_target_partition_keys(target_endpoint, partitioned) if partitioned else {}
            )

            plans = []
            for key in chunk:
                if key not in comparable:
                    plans.append(
                        AssetCopyPlan(
                            asset_key=key, skip_reason="partitioned differently in target"
                        )
                    )
                else:
                    plans.append(
                        plan_asset_copy(
                            key,
                            chunk_source,
                            chunk_target,
                            source_endpoint.org,
                            source_deployment,
                            merge_partitions,
                            partition_keys.get(key, []),
                        )
                    )
            return plans

        keys = sorted(source_keys & target_signatures.keys(), key=lambda k: k.to_user_string())
        chunks = [keys[i : i + ASSET_CHUNK_SIZE] for i in range(0, len(keys), ASSET_CHUNK_SIZE)]
        plans = []
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            # `map` yields in submission order, so output stays sorted by asset key.
            for chunk_plans in pool.map(plan_chunk, chunks):
                for plan in chunk_plans:
                    _print_plan(plan)
                    plans.append(plan)

        to_write = [plan for plan in plans if plan.events_to_write]
        total = sum(len(plan.events_to_write) for plan in to_write)
        ui.print(
            f"\n{_count(total, 'event')} across {_count(len(to_write), 'asset')};"
            f" {_count(len(undefined_keys), 'asset')} not defined in target;"
            f" {_count(sum(1 for plan in plans if plan.skip_reason), 'asset')} skipped."
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

        limiter = RateLimiter(max_events_per_second)
        # Set by the first failed write so other workers stop before their next batch, without
        # waiting for the main thread to cancel the queue.
        stop = threading.Event()

        # Within an asset, insertion order decides "latest", so each asset is written oldest
        # first by a single worker; assets are independent of each other.
        def write(plan: AssetCopyPlan) -> AssetCopyPlan | None:
            _, target = clients.get()
            try:
                for i in range(0, len(plan.events_to_write), batch_size):
                    batch = plan.events_to_write[i : i + batch_size]
                    limiter.acquire(len(batch))
                    if stop.is_set():
                        return None
                    target.store_event_batch(batch)
            except BaseException:
                stop.set()
                raise
            return plan

        started = time.monotonic()
        written = 0
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(write, plan) for plan in to_write]
            try:
                for future in as_completed(futures):
                    plan = future.result()
                    if plan is None:  # stopped by another write's failure, which raises below
                        continue
                    written += len(plan.events_to_write)
                    ui.print(
                        f"  wrote {_count(len(plan.events_to_write), 'event')} for"
                        f" {plan.asset_key.to_user_string()} ({written}/{total})"
                    )
            except BaseException:
                # Stop queued writes; a rerun resumes from what was written.
                pool.shutdown(wait=True, cancel_futures=True)
                raise
        ui.print(f"Done: wrote {_count(written, 'event')} in {time.monotonic() - started:.0f}s.")
