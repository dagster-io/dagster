# pyright: reportPrivateImportUsage=false
from collections.abc import Iterator, Sequence

import dagster as dg
import pytest
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.instance import DagsterInstance
from dagster._time import get_current_timestamp


@pytest.fixture(name="instance")
def instance_fixture() -> Iterator[dg.DagsterInstance]:
    with dg.instance_for_test() as instance:
        yield instance


def execute_check_for_asset(
    assets=None,
    asset_checks=None,
    instance=None,
) -> dg.ExecuteInProcessResult:
    the_job = dg.define_asset_job(
        name="test_asset_job",
        selection=AssetSelection.checks(*(asset_checks or [])),
    )

    defs = dg.Definitions(assets=assets, asset_checks=asset_checks, jobs=[the_job])
    job_def = defs.resolve_job_def("test_asset_job")
    return job_def.execute_in_process(instance=instance)


def assert_check_result(
    the_asset: AssetsDefinition,
    instance: DagsterInstance,
    freshness_checks: Sequence[dg.AssetChecksDefinition],
    severity: AssetCheckSeverity,
    expected_pass: bool,
    description_match: str | None = None,
    metadata_match: dict | None = None,
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
    partition_key: str | None = None,
    is_materialization: bool = True,
    override_timestamp: float | None = None,
    include_metadata: bool = True,
):
    klass = dg.AssetMaterialization if is_materialization else dg.AssetObservation
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
                "dagster/last_updated_timestamp": dg.TimestampMetadataValue(last_updated_timestamp)
            }
            if last_updated_timestamp and include_metadata
            else None,
            partition=partition_key,
        )
    )
