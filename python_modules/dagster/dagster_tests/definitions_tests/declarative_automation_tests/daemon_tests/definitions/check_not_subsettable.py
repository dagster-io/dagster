from typing import Iterator

import dagster as dg
from dagster._core.definitions.asset_check_spec import AssetCheckSpec

any_dep_newly_updated = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.newly_updated() | dg.AutomationCondition.will_be_requested()
)


@dg.asset(
    check_specs=[AssetCheckSpec(asset="unpartitioned", name="row_count")],
    automation_condition=dg.AutomationCondition.missing(),
)
def unpartitioned() -> dg.MaterializeResult:
    return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])


@dg.asset(
    check_specs=[
        AssetCheckSpec(asset="static", name="c1"),
        AssetCheckSpec(asset="static", name="c2"),
    ],
    automation_condition=dg.AutomationCondition.missing(),
    partitions_def=dg.StaticPartitionsDefinition(["a"]),
)
def static() -> dg.MaterializeResult:
    return dg.MaterializeResult(
        check_results=[
            dg.AssetCheckResult(passed=True, check_name="c1"),
            dg.AssetCheckResult(passed=True, check_name="c2"),
        ],
    )


@dg.multi_asset(
    specs=[
        dg.AssetSpec("a"),
        dg.AssetSpec("b", deps=["a"]),
        dg.AssetSpec(
            "c",
            deps=["b"],
            automation_condition=dg.AutomationCondition.missing()
            & dg.AutomationCondition.in_latest_time_window(),
        ),
        dg.AssetSpec("d", deps=["a", "c"]),
    ],
    check_specs=[
        dg.AssetCheckSpec(asset="a", name="1"),
        dg.AssetCheckSpec(asset="a", name="2"),
        dg.AssetCheckSpec(asset="d", name="3"),
    ],
    partitions_def=dg.DailyPartitionsDefinition(start_date="2024-01-01"),
)
def time_assets() -> Iterator[dg.MaterializeResult]:
    yield dg.MaterializeResult(
        asset_key="a",
        check_results=[
            dg.AssetCheckResult(passed=True, asset_key="a", check_name="1"),
            dg.AssetCheckResult(passed=True, asset_key="a", check_name="2"),
        ],
    )
    yield dg.MaterializeResult(asset_key="b")
    yield dg.MaterializeResult(asset_key="c")
    yield dg.MaterializeResult(
        asset_key="d",
        check_results=[
            dg.AssetCheckResult(passed=True, asset_key="d", check_name="3"),
        ],
    )


defs = dg.Definitions(assets=[unpartitioned, static, time_assets])
