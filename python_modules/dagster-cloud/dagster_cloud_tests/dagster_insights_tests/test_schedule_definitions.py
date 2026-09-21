from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

import pytest
from dagster import Definitions, RunRequest, build_schedule_context
from dagster._core.test_utils import freeze_time
from dagster._time import create_datetime, get_current_datetime
from dagster_cloud.dagster_insights import create_snowflake_insights_asset_and_schedule

if TYPE_CHECKING:
    from collections.abc import Iterable


@pytest.mark.parametrize("additional_schedule_offset", [0, 1, 2])
def test_schedule_definition(additional_schedule_offset: int) -> Any:
    for hour in range(0, 24):
        for minute in range(0, 60, 5):
            freeze_datetime = create_datetime(2023, 2, 27, hour, minute, 0, 0, tz="UTC")

            with freeze_time(freeze_datetime):
                start_date = (get_current_datetime() - timedelta(days=5)).replace(
                    minute=0, second=0, microsecond=0
                )

                asset_and_schedule = create_snowflake_insights_asset_and_schedule(
                    start_date=start_date,
                    name="insights_test",
                    snowflake_resource_key="snowflake_insights",
                    partition_end_offset_hrs=additional_schedule_offset,
                )

                defs = Definitions(
                    assets=asset_and_schedule.assets,
                    schedules=[asset_and_schedule.schedule],
                    resources={"snowflake_insights": None},
                )
                resolved_schedule = defs.resolve_schedule_def("snowflake_insights_import_schedule")

                execution_time = (get_current_datetime() - timedelta(hours=1)).replace(
                    minute=59, second=0, microsecond=0
                )
                result = resolved_schedule(
                    build_schedule_context(scheduled_execution_time=execution_time)
                )
                assert isinstance(result, RunRequest)

                assert result.partition_key == (
                    execution_time - timedelta(hours=1 + additional_schedule_offset)
                ).strftime("%Y-%m-%d-%H:00")


@pytest.mark.parametrize("additional_schedule_offset", [0, 1, 2])
def test_schedule_definition_group(additional_schedule_offset: int) -> Any:
    for group_hours in [2, 4, 8, 12, 24]:
        for hour in range(0, 24):
            for minute in range(0, 60, 5):
                freeze_datetime = create_datetime(2023, 2, 27, hour, minute, 0, 0, tz="UTC")

                with freeze_time(freeze_datetime):
                    start_date = (get_current_datetime() - timedelta(days=5)).replace(
                        minute=0, second=0, microsecond=0
                    )

                    asset_and_schedule = create_snowflake_insights_asset_and_schedule(
                        start_date=start_date,
                        name="insights_test",
                        snowflake_resource_key="snowflake_insights",
                        schedule_batch_size_hrs=group_hours,
                        partition_end_offset_hrs=additional_schedule_offset,
                    )

                    defs = Definitions(
                        assets=asset_and_schedule.assets,
                        schedules=[asset_and_schedule.schedule],
                        resources={"snowflake_insights": None},
                    )
                    resolved_schedule = defs.resolve_schedule_def(
                        f"snowflake_insights_import_schedule_{group_hours}_hrs"
                    )

                    execution_time = (get_current_datetime() - timedelta(hours=1)).replace(
                        minute=59, second=0, microsecond=0
                    )
                    raw_results = resolved_schedule(
                        build_schedule_context(scheduled_execution_time=execution_time)
                    )
                    assert raw_results is not None
                    results = list(cast("Iterable[RunRequest]", raw_results))

                    assert len(results) == 1
                    assert isinstance(results[0], RunRequest)

                    # Ensure we request a single run for the entire group
                    assert results[0].partition_key_range and results[
                        0
                    ].partition_key_range.start == (
                        execution_time
                        - timedelta(hours=1 + additional_schedule_offset + group_hours - 1)
                    ).strftime("%Y-%m-%d-%H:00")

                    assert results[0].partition_key_range.end == (
                        execution_time - timedelta(hours=1 + additional_schedule_offset)
                    ).strftime("%Y-%m-%d-%H:00")
