# pyright: reportPrivateImportUsage=false
import logging
from typing import Iterator, Optional, Sequence

import pendulum
import pytest
from dagster import (
    define_asset_job,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.definitions.metadata import TimestampMetadataValue
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from mock import patch


@pytest.fixture(name="instance")
def instance_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test() as instance:
        yield instance


@pytest.fixture(name="pendulum_aware_report_dagster_event")
def pendulum_aware_report_dagster_event_fixture() -> Iterator[None]:
    def pendulum_aware_report_dagster_event(
        self,
        dagster_event,
        run_id,
        log_level=logging.INFO,
    ) -> None:
        """If pendulum.test() is active, intercept event log records to have a timestamp no greater than the frozen time.

        This works best if you have a frozen time that is far in the past, so the decision to use the frozen time is clear.
        """
        event_record = EventLogEntry(
            user_message="",
            level=log_level,
            job_name=dagster_event.job_name,
            run_id=run_id,
            error_info=None,
            timestamp=pendulum.now("UTC").timestamp(),
            step_key=dagster_event.step_key,
            dagster_event=dagster_event,
        )
        self.handle_new_event(event_record)

    with patch(
        "dagster._core.instance.DagsterInstance.report_dagster_event",
        pendulum_aware_report_dagster_event,
    ):
        yield


def execute_check_for_asset(
    assets=None,
    asset_checks=None,
    instance=None,
) -> ExecuteInProcessResult:
    the_job = define_asset_job(
        name="test_asset_job",
        selection=AssetSelection.checks(*asset_checks),
    )

    defs = Definitions(assets=assets, asset_checks=asset_checks, jobs=[the_job])
    job_def = defs.get_job_def("test_asset_job")
    return job_def.execute_in_process(instance=instance)


def assert_check_result(
    the_asset: AssetsDefinition,
    instance: DagsterInstance,
    freshness_checks: Sequence[AssetChecksDefinition],
    severity: AssetCheckSeverity,
    expected_pass: bool,
    description_match: Optional[str] = None,
) -> None:
    result = execute_check_for_asset(
        assets=[the_asset],
        asset_checks=freshness_checks,
        instance=instance,
    )
    assert result.success
    assert len(result.get_asset_check_evaluations()) == 1
    assert result.get_asset_check_evaluations()[0].passed == expected_pass
    assert result.get_asset_check_evaluations()[0].severity == severity
    if description_match:
        description = result.get_asset_check_evaluations()[0].description
        assert description
        assert description_match in description


def add_new_event(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partition_key: Optional[str] = None,
    is_materialization: bool = True,
):
    klass = AssetMaterialization if is_materialization else AssetObservation
    metadata = (
        {"dagster/last_updated_timestamp": TimestampMetadataValue(pendulum.now("UTC").timestamp())}
        if not is_materialization
        else None
    )
    instance.report_runless_asset_event(
        klass(
            asset_key=asset_key,
            metadata=metadata,
            partition=partition_key,
        )
    )
