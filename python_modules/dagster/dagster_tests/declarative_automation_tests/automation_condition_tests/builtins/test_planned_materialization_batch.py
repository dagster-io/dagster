from unittest import mock

import dagster as dg
import pytest
import sqlalchemy as db
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.remote_origin import (
    GrpcServerCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES, DagsterRunStatus
from dagster._core.storage.event_log.base import AssetEntry, AssetRecord
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from sqlalchemy import event as sqlalchemy_event

from dagster_tests.declarative_automation_tests.automation_condition_tests.builtins.test_failed_condition import (
    _add_event_to_run,
    _materialization_event,
    _materialization_planned_event,
)


@pytest.mark.parametrize("count", [1, 8])
def test_missing_and_in_progress_share_prefetched_snapshot(count: int) -> None:
    defs = _defs(dg.AutomationCondition.missing() & ~dg.AutomationCondition.in_progress(), count)
    keys = list(defs.resolve_asset_graph().get_all_asset_keys())
    original = CachingInstanceQueryer.prefetch_asset_records
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(job_name="job", status=DagsterRunStatus.STARTED)
        instance.add_run(run)
        for key in keys:
            _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))

        def interleaved_prefetch(queryer, asset_keys):
            original(queryer, asset_keys)
            for key in keys:
                _add_event_to_run(instance, run.run_id, _materialization_event(key))

        storage = instance.event_log_storage
        with (
            mock.patch.object(
                CachingInstanceQueryer, "prefetch_asset_records", interleaved_prefetch
            ),
            mock.patch.object(
                storage,
                "get_latest_planned_materialization_info",
                side_effect=AssertionError("singular read"),
            ),
            mock.patch.object(
                storage,
                "get_latest_planned_materialization_info_for_keys",
                wraps=storage.get_latest_planned_materialization_info_for_keys,
            ) as batch,
        ):
            result = dg.evaluate_automation_conditions(defs, instance=instance)
            assert result.total_requested == 0
            assert batch.call_count == 1
            assert set(batch.call_args.args[0]) == set(keys)
        assert (
            dg.evaluate_automation_conditions(
                defs, instance=instance, cursor=result.cursor
            ).total_requested
            == 0
        )


def _defs(condition: dg.AutomationCondition, count: int = 1) -> dg.Definitions:
    return dg.Definitions(
        assets=[
            dg.asset(name=f"asset_{i}", automation_condition=condition)(lambda: None)
            for i in range(count)
        ]
    )


@pytest.mark.parametrize("count", [1, 8, 64])
@pytest.mark.parametrize("condition_name", ["execution_failed", "in_progress", "both"])
def test_planned_reads_batch_across_conditions(count: int, condition_name: str) -> None:
    failed = dg.AutomationCondition.execution_failed()
    progress = dg.AutomationCondition.in_progress()
    condition = (
        failed | progress
        if condition_name == "both"
        else (failed if condition_name == "execution_failed" else progress)
    )
    defs = _defs(condition, count)
    keys = list(defs.resolve_asset_graph().get_all_asset_keys())
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(
            job_name="job",
            status=DagsterRunStatus.FAILURE
            if condition_name == "execution_failed"
            else DagsterRunStatus.STARTED,
        )
        instance.add_run(run)
        for key in keys:
            _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        statements = []

        def record_query(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith(
                "SELECT"
            ) and "ASSET_MATERIALIZATION_PLANNED" in str(parameters):
                statements.append(statement)

        storage = instance.event_log_storage
        sqlalchemy_event.listen(db.engine.Engine, "before_cursor_execute", record_query)
        try:
            with (
                mock.patch.object(
                    storage,
                    "get_latest_planned_materialization_info",
                    side_effect=AssertionError("singular read"),
                ),
                mock.patch.object(
                    storage,
                    "get_latest_planned_materialization_info_for_keys",
                    wraps=storage.get_latest_planned_materialization_info_for_keys,
                ) as batch,
            ):
                result = dg.evaluate_automation_conditions(defs, instance=instance)
                assert result.total_requested == count
                assert batch.call_count == 1
                assert set(batch.call_args.args[0]) == set(keys)
                assert len(statements) == 1

                # A new evaluation must not reuse the old planned event or RunRecord.
                new_run = dg.DagsterRun(job_name="job", status=DagsterRunStatus.SUCCESS)
                instance.add_run(new_run)
                for key in keys:
                    _add_event_to_run(instance, new_run.run_id, _materialization_planned_event(key))
                result = dg.evaluate_automation_conditions(
                    defs, instance=instance, cursor=result.cursor
                )
                assert result.total_requested == 0
                assert batch.call_count == 2
                assert len(statements) == 2
        finally:
            sqlalchemy_event.remove(db.engine.Engine, "before_cursor_execute", record_query)


@pytest.mark.parametrize("status", list(DagsterRunStatus))
@pytest.mark.parametrize("materialized", [False, True])
@pytest.mark.asyncio
async def test_in_progress_matches_sync_queryer(
    status: DagsterRunStatus, materialized: bool
) -> None:
    defs = _defs(dg.AutomationCondition.in_progress())
    key = dg.AssetKey("asset_0")
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(
            job_name="job",
            status=status,
            remote_job_origin=RemoteJobOrigin(
                RemoteRepositoryOrigin(
                    GrpcServerCodeLocationOrigin("localhost", port=1234), "repo"
                ),
                "job",
            ),
        )
        instance.add_run(run)
        _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        if materialized:
            _add_event_to_run(instance, run.run_id, _materialization_event(key))
        view = AssetGraphView.for_test(defs, instance=instance)
        queryer = CachingInstanceQueryer(instance, defs.resolve_asset_graph(), view)
        expected = not materialized and status in [
            *IN_PROGRESS_RUN_STATUSES,
            DagsterRunStatus.QUEUED,
        ]
        assert queryer.get_in_progress_asset_subset(asset_key=key).value == expected
        subset = await view.compute_run_in_progress_subset(
            key=key, from_subset=view.get_full_subset(key=key)
        )
        assert bool(subset.size) == expected


@pytest.mark.parametrize("record_kind", ["missing", "no_plan", "planned", "materialized"])
def test_in_progress_cloud_fast_path(record_kind: str) -> None:
    defs = _defs(dg.AutomationCondition.in_progress())
    key = dg.AssetKey("asset_0")
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(job_name="job", status=DagsterRunStatus.STARTED)
        instance.add_run(run)
        _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        if record_kind == "materialized":
            _add_event_to_run(instance, run.run_id, _materialization_event(key))
        materialization = instance.get_asset_records([key])[
            0
        ].asset_entry.last_materialization_record
        records = (
            []
            if record_kind == "missing"
            else [
                AssetRecord(
                    storage_id=1,
                    asset_entry=AssetEntry(
                        asset_key=key,
                        last_planned_materialization_run_id=run.run_id
                        if record_kind != "no_plan"
                        else None,
                        last_materialization_record=materialization,
                    ),
                )
            ]
        )
        storage = instance.event_log_storage
        with (
            mock.patch.object(
                type(storage),
                "asset_records_have_last_planned_and_failed_materializations",
                new_callable=mock.PropertyMock,
                return_value=True,
            ),
            mock.patch.object(storage, "get_asset_records", return_value=records),
            mock.patch.object(
                storage,
                "get_latest_planned_materialization_info_for_keys",
                side_effect=AssertionError("cloud must not fetch plans"),
            ),
            mock.patch.object(
                storage,
                "get_latest_planned_materialization_info",
                side_effect=AssertionError("cloud must not fetch plans"),
            ),
        ):
            result = dg.evaluate_automation_conditions(defs, instance=instance)
            assert result.total_requested == (1 if record_kind == "planned" else 0)


def test_failed_finds_earlier_materialization_in_same_run() -> None:
    defs = _defs(dg.AutomationCondition.execution_failed())
    key = dg.AssetKey("asset_0")
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(job_name="job", status=DagsterRunStatus.FAILURE)
        instance.add_run(run)
        _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        _add_event_to_run(instance, run.run_id, _materialization_event(key))
        for i in range(3):
            _add_event_to_run(instance, f"other_{i}", _materialization_event(key))
        with mock.patch("dagster._utils.storage.get_materialization_chunk_size", return_value=1):
            assert dg.evaluate_automation_conditions(defs, instance=instance).total_requested == 0


def test_in_progress_only_considers_latest_planned_run() -> None:
    defs = _defs(dg.AutomationCondition.in_progress())
    key = dg.AssetKey("asset_0")
    with dg.DagsterInstance.ephemeral() as instance:
        for status in [DagsterRunStatus.STARTED, DagsterRunStatus.SUCCESS]:
            run = dg.DagsterRun(job_name="job", status=status)
            instance.add_run(run)
            _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        assert dg.evaluate_automation_conditions(defs, instance=instance).total_requested == 0


@pytest.mark.parametrize(
    "condition", [dg.AutomationCondition.execution_failed(), dg.AutomationCondition.in_progress()]
)
def test_missing_planned_run(condition: dg.AutomationCondition) -> None:
    defs = _defs(condition)
    with dg.DagsterInstance.ephemeral() as instance:
        assert dg.evaluate_automation_conditions(defs, instance=instance).total_requested == 0
        _add_event_to_run(
            instance, "missing", _materialization_planned_event(dg.AssetKey("asset_0"))
        )
        assert dg.evaluate_automation_conditions(defs, instance=instance).total_requested == 0


def test_planned_reads_dispatch_per_topological_level() -> None:
    condition = dg.AutomationCondition.execution_failed() | dg.AutomationCondition.in_progress()
    keys = [dg.AssetKey(f"asset_{i}") for i in range(3)]
    defs = dg.Definitions(
        assets=[
            dg.asset(
                name=key.to_user_string(),
                deps=keys[i - 1 : i] if i else [],
                automation_condition=condition,
            )(lambda: None)
            for i, key in enumerate(keys)
        ]
    )
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(job_name="job", status=DagsterRunStatus.STARTED)
        instance.add_run(run)
        for key in keys:
            _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        storage = instance.event_log_storage
        with mock.patch.object(
            storage,
            "get_latest_planned_materialization_info_for_keys",
            wraps=storage.get_latest_planned_materialization_info_for_keys,
        ) as batch:
            assert dg.evaluate_automation_conditions(defs, instance=instance).total_requested == 3
            # Evaluation gathers a frontier, not the entire dependency graph at once.
            assert [list(call.args[0]) for call in batch.call_args_list] == [[key] for key in keys]


@pytest.mark.parametrize("partitioned", [False, True])
def test_partitioned_and_backfill_paths_do_not_load_plans(partitioned: bool) -> None:
    condition = (
        dg.AutomationCondition.execution_failed() | dg.AutomationCondition.in_progress()
        if partitioned
        else dg.AutomationCondition.backfill_in_progress()
    )

    @dg.asset(
        automation_condition=condition,
        partitions_def=dg.StaticPartitionsDefinition(["a", "b"]) if partitioned else None,
    )
    def asset(): ...

    with dg.DagsterInstance.ephemeral() as instance:
        with mock.patch.object(
            instance.event_log_storage,
            "get_latest_planned_materialization_info_for_keys",
            side_effect=AssertionError("unpartitioned loader used"),
        ):
            assert (
                dg.evaluate_automation_conditions(
                    dg.Definitions(assets=[asset]), instance=instance
                ).total_requested
                == 0
            )


@pytest.mark.parametrize("condition_name", ["execution_failed", "in_progress"])
def test_next_tick_observes_updated_run_status(condition_name: str) -> None:
    defs = _defs(getattr(dg.AutomationCondition, condition_name)())
    key = dg.AssetKey("asset_0")
    with dg.DagsterInstance.ephemeral() as instance:
        run = dg.DagsterRun(job_name="job", status=DagsterRunStatus.STARTED)
        instance.add_run(run)
        _add_event_to_run(instance, run.run_id, _materialization_planned_event(key))
        result = dg.evaluate_automation_conditions(defs, instance=instance)
        assert result.total_requested == (1 if condition_name == "in_progress" else 0)
        instance.report_run_failed(run)
        result = dg.evaluate_automation_conditions(defs, instance=instance, cursor=result.cursor)
        assert result.total_requested == (1 if condition_name == "execution_failed" else 0)
        instance.delete_run(run.run_id)
        assert (
            dg.evaluate_automation_conditions(
                defs, instance=instance, cursor=result.cursor
            ).total_requested
            == 0
        )
