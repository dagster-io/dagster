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
                    asset_key=ASSET_KEY, partition=partition, metadata={"rows": 3}, tags=tags
                )
            ),
        ),
    )
    return EventLogRecord(storage_id=storage_id, event_log_entry=entry)


class FakeStorage:
    def __init__(self, records: list[EventLogRecord]):
        self._records = records

    def _latest_by_partition(self) -> dict[str, EventLogRecord]:
        latest = {}
        for record in sorted(self._records, key=lambda r: r.storage_id):
            if record.partition_key is not None:
                latest[record.partition_key] = record
        return latest

    def get_latest_storage_id_by_partition(self, asset_key, event_type):
        return {p: r.storage_id for p, r in self._latest_by_partition().items()}

    def fetch_materializations(self, records_filter, limit, cursor=None):
        if isinstance(records_filter, AssetKey):
            rows = sorted(self._records, key=lambda r: -r.storage_id)
        else:
            ids = set(records_filter.storage_ids)
            rows = [r for r in self._records if r.storage_id in ids]
        return EventRecordsResult(records=rows[:limit], cursor="", has_more=False)

    def get_materialized_partitions(self, asset_key):
        return set(self._latest_by_partition())

    def get_latest_materialization_events(self, asset_keys):
        if not self._records:
            return {}
        return {ASSET_KEY: max(self._records, key=lambda r: r.storage_id).event_log_entry}


def _plan(source_records, target_records, merge_partitions=False, partition_keys=({"a", "b"},)):
    return plan_asset_copy(
        ASSET_KEY,
        FakeStorage(source_records),  # ty: ignore[invalid-argument-type]
        FakeStorage(target_records),  # ty: ignore[invalid-argument-type]
        "source-org",
        "prod",
        merge_partitions,
        partition_keys,
    )


def _partitions(plan):
    return [e.asset_materialization.partition for e in plan.events_to_write]


def test_copied_entry_keeps_timestamp_and_tags_source():
    entry = build_copied_event(
        _record(7, "2024-01-01", 1700000000.0, {"k": "v"}), "source-org", "prod"
    )

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
        return [ASSET_KEY]

    def store_event_batch(self, events):
        self.written.extend(events)


SIGNATURE = (("default", "STATIC", None),)


def _invoke(monkeypatch, args, confirm, source_signature=SIGNATURE):
    source = RecordingStorage([_record(1, "a", 10.0)])
    target = RecordingStorage([])
    storages = iter([source, target])
    prompts = []

    def _confirm(prompt, default=True):
        prompts.append(prompt)
        return confirm

    def _signatures(endpoint):
        return {ASSET_KEY: source_signature if endpoint.org == "source-org" else SIGNATURE}

    monkeypatch.setattr(
        copy_materializations, "_create_event_log_storage", lambda *args: next(storages)
    )
    monkeypatch.setattr(copy_materializations, "_fetch_partition_signatures", _signatures)
    monkeypatch.setattr(
        copy_materializations, "_fetch_target_partition_keys", lambda *args: [{"a"}]
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
            *args,
        ],
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
