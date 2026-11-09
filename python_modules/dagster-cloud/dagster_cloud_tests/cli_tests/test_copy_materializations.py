import threading
from collections import Counter

from dagster import AssetKey, AssetMaterialization
from dagster._core.event_api import EventLogRecord, EventRecordsResult
from dagster._core.events import DagsterEvent, DagsterEventType, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.instance.utils import RUNLESS_RUN_ID
from dagster_cloud import copy_materializations
from dagster_cloud.copy_materializations import (
    SOURCE_RUN_ID_TAG,
    build_copied_event,
    plan_asset_copy,
)
from typer import Typer
from typer.testing import CliRunner

ASSET_KEY = AssetKey(["prefix", "asset"])


def _record(
    storage_id: int,
    partition: str | None,
    timestamp: float,
    tags: dict[str, str] | None = None,
    asset_key: AssetKey = ASSET_KEY,
) -> EventLogRecord:
    entry = EventLogEntry(
        user_message="",
        level=20,
        job_name="job",
        run_id=f"run-{storage_id}",
        error_info=None,
        timestamp=timestamp,
        step_key=None,
        dagster_event=DagsterEvent(
            event_type_value=DagsterEventType.ASSET_MATERIALIZATION.value,
            job_name="job",
            event_specific_data=StepMaterializationData(
                AssetMaterialization(
                    asset_key=asset_key, partition=partition, metadata={"rows": 3}, tags=tags
                )
            ),
        ),
    )
    return EventLogRecord(storage_id=storage_id, event_log_entry=entry)


def _asset_key(record: EventLogRecord) -> AssetKey | None:
    materialization = record.asset_materialization
    return materialization.asset_key if materialization is not None else None


class FakeStorage:
    def __init__(self, records: list[EventLogRecord]):
        self._records = records
        self._lock = threading.Lock()
        self.calls: Counter[str] = Counter()

    def _count(self, name):
        with self._lock:
            self.calls[name] += 1

    def _for(self, asset_key):
        return [r for r in self._records if _asset_key(r) == asset_key]

    def _latest_by_partition(self, asset_key) -> dict[str, EventLogRecord]:
        latest = {}
        for record in sorted(self._for(asset_key), key=lambda r: r.storage_id):
            if record.partition_key is not None:
                latest[record.partition_key] = record
        return latest

    def get_latest_storage_id_by_partition(self, asset_key, event_type):
        self._count("get_latest_storage_id_by_partition")
        return {p: r.storage_id for p, r in self._latest_by_partition(asset_key).items()}

    def fetch_materializations(self, records_filter, limit, cursor=None):
        self._count("fetch_materializations")
        ids = set(records_filter.storage_ids)
        rows = [r for r in self._for(records_filter.asset_key) if r.storage_id in ids]
        return EventRecordsResult(records=rows[:limit], cursor="", has_more=False)

    def get_materialized_partitions(self, asset_key):
        self._count("get_materialized_partitions")
        return set(self._latest_by_partition(asset_key))

    def get_latest_materialization_events(self, asset_keys):
        self._count("get_latest_materialization_events")
        latest = {}
        for key in asset_keys:
            records = self._for(key)
            if records:
                latest[key] = max(records, key=lambda r: r.storage_id).event_log_entry
        return latest


def _plan(
    source_records,
    target_records,
    merge_partitions=False,
    partition_keys=({"a", "b"},),
    source=None,
    target=None,
):
    return plan_asset_copy(
        ASSET_KEY,
        source if source is not None else FakeStorage(source_records),  # ty: ignore[invalid-argument-type]
        target if target is not None else FakeStorage(target_records),  # ty: ignore[invalid-argument-type]
        "source-org",
        "prod",
        merge_partitions,
        partition_keys,
    )


def _partitions(plan):
    return [e.asset_materialization.partition for e in plan.events_to_write]


def test_copied_entry_keeps_timestamp_and_tags_source():
    record = _record(7, "2024-01-01", 1700000000.0, {"k": "v"})
    entry = build_copied_event(record.event_log_entry, "source-org", "prod")

    assert entry.run_id == RUNLESS_RUN_ID
    assert entry.timestamp == 1700000000.0
    materialization = entry.asset_materialization
    assert materialization is not None
    assert materialization.partition == "2024-01-01"
    assert materialization.metadata["rows"].value == 3
    assert materialization.tags == {
        "k": "v",
        "migration/source_org": "source-org",
        "migration/source_deployment": "prod",
        SOURCE_RUN_ID_TAG: "run-7",
    }


def test_copies_latest_per_partition_oldest_first():
    source = [
        _record(1, "a", 10.0),
        _record(2, "b", 20.0),
        _record(3, "a", 30.0),
    ]

    plan = _plan(source, [])

    assert plan.skip_reason is None
    assert _partitions(plan) == ["b", "a"]
    assert [e.timestamp for e in plan.events_to_write] == [20.0, 30.0]


def test_skips_asset_with_native_target_materializations():
    plan = _plan([_record(1, "a", 10.0), _record(2, "b", 20.0)], [_record(1, "b", 50.0)])

    assert plan.skip_reason == "target already has its own materializations"
    assert plan.events_to_write == []


def test_merge_partitions_fills_only_missing_partitions():
    plan = _plan(
        [_record(1, "a", 10.0), _record(2, "b", 20.0)],
        [_record(1, "b", 50.0)],
        merge_partitions=True,
    )

    assert _partitions(plan) == ["a"]
    assert plan.already_in_target == 1


def test_skips_asset_materialized_by_target_after_a_copy():
    target = [_record(1, "a", 10.0, {SOURCE_RUN_ID_TAG: "run-1"}), _record(2, "b", 50.0)]

    plan = _plan([_record(1, "a", 10.0), _record(2, "b", 20.0)], target)

    assert plan.skip_reason == "target already has its own materializations"


def test_rerun_resumes_after_partial_copy():
    target = [_record(1, "a", 10.0, {SOURCE_RUN_ID_TAG: "run-1"})]

    plan = _plan([_record(1, "a", 10.0), _record(2, "b", 20.0)], target)

    assert plan.skip_reason is None
    assert _partitions(plan) == ["b"]


def test_unpartitioned_asset():
    plan = _plan([_record(1, None, 10.0), _record(2, None, 20.0)], [], partition_keys=())
    assert [e.timestamp for e in plan.events_to_write] == [20.0]

    plan = _plan([_record(1, None, 10.0)], [_record(1, None, 50.0)], partition_keys=())
    assert plan.skip_reason is not None


def test_skips_partitions_missing_from_target():
    plan = _plan(
        [_record(1, "a", 10.0), _record(2, "b", 20.0), _record(3, "c", 30.0)],
        [],
        partition_keys=({"a"},),
    )

    assert _partitions(plan) == ["a"]
    assert plan.missing_from_target == 2


def test_fetches_only_partitions_to_copy():
    source = FakeStorage([_record(i, f"p{i}", float(i)) for i in range(250)])

    plan = _plan(None, [], partition_keys=({"p0", "p1"},), source=source)

    assert _partitions(plan) == ["p0", "p1"]
    assert plan.missing_from_target == 248
    assert source.calls["fetch_materializations"] == 1


def test_skipped_asset_fetches_no_events():
    source = FakeStorage([_record(1, "a", 10.0)])

    plan = _plan(None, [_record(1, "b", 50.0)], source=source)

    assert plan.skip_reason == "target already has its own materializations"
    assert source.calls["fetch_materializations"] == 0


def test_skips_partition_read_when_target_never_materialized():
    target = FakeStorage([])

    plan = _plan([_record(1, "a", 10.0)], None, target=target)

    assert _partitions(plan) == ["a"]
    assert target.calls["get_materialized_partitions"] == 0


def test_checks_multipartition_keys_per_dimension():
    plan = _plan(
        [_record(1, "x|1", 10.0), _record(2, "y|1", 20.0), _record(3, "x|2", 30.0)],
        [],
        partition_keys=({"x"}, {"1", "2"}),
    )

    assert _partitions(plan) == ["x|1", "x|2"]
    assert plan.missing_from_target == 1


def test_skips_partitioned_events_for_unpartitioned_target():
    plan = _plan([_record(1, "a", 10.0)], [], partition_keys=())

    assert plan.events_to_write == []
    assert plan.missing_from_target == 1


class RecordingStorage(FakeStorage):
    def __init__(self, records: list[EventLogRecord]):
        super().__init__(records)
        self.written: list[EventLogEntry] = []

    def all_asset_keys(self):
        return list({_asset_key(r) for r in self._records})

    def store_event_batch(self, events):
        with self._lock:
            self.written.extend(events)


class FailingStorage(RecordingStorage):
    def store_event_batch(self, events):
        self._count("store_event_batch")
        raise RuntimeError("write failed")


SIGNATURE = (("default", "STATIC", None),)


def _run(
    monkeypatch,
    args,
    confirm=True,
    source_records=None,
    signatures=None,
    source_signature=None,
    partition_keys=({"a"},),
    fail_writes=False,
):
    source = RecordingStorage(
        source_records if source_records is not None else [_record(1, "a", 10.0)]
    )
    target = FailingStorage([]) if fail_writes else RecordingStorage([])
    target_signatures = signatures if signatures is not None else {ASSET_KEY: SIGNATURE}
    prompts = []

    def _confirm(prompt, default=True):
        prompts.append(prompt)
        return confirm

    def _signatures(endpoint):
        if endpoint.org == "source-org" and source_signature is not None:
            return source_signature
        return target_signatures

    monkeypatch.setattr(
        copy_materializations,
        "_create_event_log_storage",
        lambda session, endpoint: source if endpoint.org == "source-org" else target,
    )
    monkeypatch.setattr(copy_materializations, "_fetch_partition_signatures", _signatures)
    monkeypatch.setattr(
        copy_materializations,
        "_fetch_target_partition_keys",
        lambda endpoint, asset_keys: {key: list(partition_keys) for key in asset_keys},
    )
    monkeypatch.setattr(copy_materializations.ui, "confirm", _confirm)

    app = Typer()
    app.command()(copy_materializations.copy_materializations_command)
    result = CliRunner().invoke(
        app,
        [
            "--source-deployment",
            "prod",
            "--target-deployment",
            "prod",
            "--source-agent-token",
            "source-token",
            "--target-agent-token",
            "target-token",
            "--source-url",
            "https://source-org.dagster.cloud",
            "--target-url",
            "https://target-org.dagster.cloud",
            # Throttling is covered by the rate limiter test; don't sleep here.
            "--max-events-per-second",
            "1000000",
            *args,
        ],
    )
    return result, source, target, prompts


def _invoke(monkeypatch, args, confirm, source_signature=SIGNATURE):
    result, _, target, prompts = _run(
        monkeypatch, args, confirm, source_signature={ASSET_KEY: source_signature}
    )
    assert result.exit_code == 0, result.output
    return target.written, prompts, result.output


def test_dry_run_does_not_prompt_or_write(monkeypatch):
    written, prompts, _ = _invoke(monkeypatch, ["--dry-run"], confirm=True)

    assert prompts == []
    assert written == []


def test_declining_confirmation_writes_nothing(monkeypatch):
    written, prompts, _ = _invoke(monkeypatch, [], confirm=False)

    assert prompts == ["Do you want to continue?"]
    assert written == []


def test_confirming_writes_events(monkeypatch):
    written, _, _ = _invoke(monkeypatch, [], confirm=True)

    assert [e.asset_materialization.partition for e in written] == ["a"]


def test_skips_assets_partitioned_differently_in_target(monkeypatch):
    written, prompts, output = _invoke(monkeypatch, [], confirm=True, source_signature=None)

    assert "partitioned differently in target" in output
    assert prompts == []
    assert written == []


def test_reads_latest_materializations_once_per_chunk(monkeypatch):
    keys = [AssetKey(f"asset_{i:03d}") for i in range(150)]
    records = [_record(i, None, float(i), asset_key=key) for i, key in enumerate(keys)]

    result, source, target, _ = _run(
        monkeypatch, [], source_records=records, signatures={key: None for key in keys}
    )

    assert result.exit_code == 0, result.output
    assert len(target.written) == 150
    # Two chunks of up to 100 assets: one read per chunk and side, none per asset.
    assert source.calls == Counter({"get_latest_materialization_events": 2})
    assert target.calls == Counter({"get_latest_materialization_events": 2})


def test_prefetched_event_log_serves_prefetched_assets_without_requests():
    other = AssetKey("other")
    storage = FakeStorage([_record(1, None, 10.0), _record(2, None, 20.0, asset_key=other)])
    prefetched = copy_materializations.PrefetchedEventLog(storage, [ASSET_KEY])  # ty: ignore[invalid-argument-type]

    prefetched_event = prefetched.get_latest_materialization_events([ASSET_KEY])[ASSET_KEY]
    assert prefetched_event is not None and prefetched_event.timestamp == 10.0
    assert storage.calls["get_latest_materialization_events"] == 1

    other_event = prefetched.get_latest_materialization_events([other])[other]
    assert other_event is not None and other_event.timestamp == 20.0
    assert storage.calls["get_latest_materialization_events"] == 2


def test_rejects_batch_size_above_server_limit(monkeypatch):
    result, _, target, _ = _run(monkeypatch, ["--batch-size", "51"])

    assert result.exit_code != 0
    assert target.written == []


def test_target_partition_keys_are_read_in_chunks(monkeypatch):
    requests = []

    def _query(endpoint, query, variables):
        paths = [key["path"] for key in variables["assetKeys"]]
        requests.append(paths)
        return {
            "assetNodes": [
                {
                    "assetKey": {"path": path},
                    "partitionKeysByDimension": [
                        {"name": "b", "partitionKeys": ["1"]},
                        {"name": "a", "partitionKeys": ["x"]},
                    ],
                }
                for path in paths
            ]
        }

    monkeypatch.setattr(copy_materializations, "_query_webserver", _query)
    keys = [AssetKey(f"asset_{i}") for i in range(60)]

    keys_by_asset = copy_materializations._fetch_target_partition_keys(  # noqa: SLF001
        copy_materializations.resolve_endpoint("token", "prod", "https://my-org.dagster.cloud"),
        keys,
    )

    assert [len(paths) for paths in requests] == [25, 25, 10]
    assert keys_by_asset[keys[0]] == [{"x"}, {"1"}]


def test_concurrent_writes_keep_each_asset_oldest_first(monkeypatch):
    keys = [AssetKey(f"asset_{i}") for i in range(8)]
    records = [
        _record(i * 10 + j, f"p{j}", float(100 - j), asset_key=key)
        for i, key in enumerate(keys)
        for j in range(5)
    ]

    result, _, target, _ = _run(
        monkeypatch,
        ["--concurrency", "4", "--batch-size", "2"],
        source_records=records,
        signatures={key: SIGNATURE for key in keys},
        partition_keys=({f"p{j}" for j in range(5)},),
    )

    assert result.exit_code == 0, result.output
    assert len(target.written) == 40
    for key in keys:
        timestamps = [
            e.timestamp for e in target.written if e.asset_materialization.asset_key == key
        ]
        assert timestamps == sorted(timestamps)


def test_failed_write_stops_the_copy(monkeypatch):
    keys = [AssetKey(f"asset_{i}") for i in range(20)]
    records = [_record(i, None, float(i), asset_key=key) for i, key in enumerate(keys)]

    result, _, target, _ = _run(
        monkeypatch,
        ["--concurrency", "1"],
        source_records=records,
        signatures={key: None for key in keys},
        fail_writes=True,
    )

    assert result.exit_code != 0
    # The first failure stops the 19 writes still queued.
    assert target.calls["store_event_batch"] == 1


def test_failed_write_stops_other_workers(monkeypatch):
    keys = [AssetKey(f"asset_{i}") for i in range(20)]
    records = [_record(i, None, float(i), asset_key=key) for i, key in enumerate(keys)]

    result, _, target, _ = _run(
        monkeypatch,
        ["--concurrency", "4"],
        source_records=records,
        signatures={key: None for key in keys},
        fail_writes=True,
    )

    assert result.exit_code != 0
    # At most one batch per worker was already in flight; none start after the failure.
    assert 1 <= target.calls["store_event_batch"] <= 4


def test_rate_limiter_spaces_units_across_calls():
    now = [0.0]
    sleeps = []

    def _sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    limiter = copy_materializations.RateLimiter(100, clock=lambda: now[0], sleep=_sleep)
    for _ in range(3):
        limiter.acquire(50)

    assert sleeps == [0.5, 0.5]


def test_endpoint_from_url():
    endpoint = copy_materializations.resolve_endpoint(
        "token", "prod", "https://my-org.dogfood.dagster.cloud/"
    )

    assert endpoint.org == "my-org"
    assert endpoint.webserver_url == "https://my-org.dogfood.dagster.cloud"
    assert endpoint.agent_url == "https://my-org.agent.dogfood.dagster.cloud"


def test_endpoint_from_token(monkeypatch):
    monkeypatch.setattr(copy_materializations, "decode_agent_token", lambda token: ("my-org", "eu"))

    endpoint = copy_materializations.resolve_endpoint("token", "prod", None)

    assert endpoint.webserver_url == "https://my-org.eu.dagster.cloud"
    assert endpoint.agent_url == "https://my-org.agent.eu.dagster.cloud"
