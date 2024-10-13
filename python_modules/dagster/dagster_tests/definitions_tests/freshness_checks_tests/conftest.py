# pyright: reportPrivateImportUsage=false
from typing import Iterator, Optional, Sequence

import pytest
from dagster import define_asset_job
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.definitions.metadata import TimestampMetadataValue
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._time import get_current_timestamp


@pytest.fixture(name="instance")
def instance_fixture() -> Iterator[DagsterInstance]:
    with instance_for_test() as instance:
        yield instance


def execute_check_for_asset(
    assets=None,
    asset_checks=None,
    instance=None,
) -> ExecuteInProcessResult:
    the_job = define_asset_job(
        name="test_asset_job",
        selection=AssetSelection.checks(*(asset_checks or [])),
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
    metadata_match: Optional[dict] = None,
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
    if metadata_match:
        metadata = result.get_asset_check_evaluations()[0].metadata
        assert metadata
        assert metadata == metadata_match


def add_new_event(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partition_key: Optional[str] = None,
    is_materialization: bool = True,
    override_timestamp: Optional[float] = None,
    include_metadata: bool = True,
):
    klass = AssetMaterialization if is_materialization else AssetObservation
    last_updated_timestamp = (
        override_timestamp
        if override_timestamp is not None
        else get_current_timestamp()
        if not is_materialization
        else None
    )
    instance.report_runless_asset_event(
        klass(
            asset_key=asset_key,
            metadata={
                "dagster/last_updated_timestamp": TimestampMetadataValue(last_updated_timestamp)
            }
            if last_updated_timestamp and include_metadata
            else None,
            partition=partition_key,
        )
    )
