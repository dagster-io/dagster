---
title: "Running a subset of asset checks"
sidebar_position: 200
---

In some cases, you may only want to execute some of the [asset checks](asset-checks) defined in a <PyObject section="assets" module="dagster" object="multi_asset" decorator /> or <PyObject section="asset-checks" module="dagster" object="multi_asset_check" decorator />. For example, you may want to materialize a <PyObject section="assets" module="dagster" object="multi_asset" decorator /> without executing the checks or only execute a certain set of checks.

In this guide, we'll show you a few approaches to subsetting asset checks in <PyObject section="asset-checks" module="dagster" object="multi_asset_check" decorator pluralize /> and <PyObject section="assets" module="dagster" object="multi_asset" decorator pluralize />.

:::note

This article assumes familiarity with [asset checks](asset-checks) and [multi-assets](/guides/build/assets/multi-assets).

:::

## Subsetting checks in @multi_asset_checks

Using the <PyObject section="asset-checks" module="dagster" object="multi_asset_check" decorator /> decorator's `specs` and `can_subset` arguments, you can execute a subset of checks in a single op.

{/* TODO link this to proper API doc */}
Inside the body of the function, we can use `AssetCheckExecutionContext.selected_asset_check_keys` to identify which computations to run. We can also set the decorator's `can_subset` parameter to `True` to execute a subset of the asset checks that the computation contains.

As we don't know in advance which checks will be executed, we explicitly `yield` each asset check result that we're expected to create:

```python file=/concepts/assets/asset_checks/subset_multi_asset_check.py
from collections.abc import Iterable

from dagster import (
    AssetCheckExecutionContext,
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    multi_asset_check,
)


@multi_asset_check(
    specs=[
        AssetCheckSpec(name="asset_check_one", asset="asset_one"),
        AssetCheckSpec(name="asset_check_two", asset="asset_two"),
    ],
    can_subset=True,
)
def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
    if (
        AssetCheckKey(AssetKey("asset_one"), "asset_check_one")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(
            passed=True, metadata={"foo": "bar"}, check_name="asset_check_one"
        )
    if (
        AssetCheckKey(AssetKey("asset_two"), "asset_check_two")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(
            passed=True, metadata={"foo": "bar"}, check_name="asset_check_two"
        )
```

## Subsetting checks in @multi_assets

When using [multi-assets](/guides/build/assets/multi-assets), Dagster assumes that all checks specified on the asset should be executed after it is materialized. This means that attempting to execute some, but not all, of the checks defined by a multi-asset will result in an error.

In the following example, we only want to execute a check when the `multi_asset_piece_1` asset produced by the `multi_asset_1_and_2` multi-asset is materialized:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/assets/asset_checks/subset_check_multi_asset.py
from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    MaterializeResult,
    multi_asset,
)


@multi_asset(
    specs=[
        AssetSpec("multi_asset_piece_1", group_name="asset_checks", skippable=True),
        AssetSpec("multi_asset_piece_2", group_name="asset_checks", skippable=True),
    ],
    check_specs=[AssetCheckSpec("my_check", asset="multi_asset_piece_1")],
    can_subset=True,
)
def multi_asset_1_and_2(context: AssetExecutionContext):
    if AssetKey("multi_asset_piece_1") in context.selected_asset_keys:
        yield MaterializeResult(asset_key="multi_asset_piece_1")
    # The check will only execute when multi_asset_piece_1 is materialized
    if (
        AssetCheckKey(AssetKey("multi_asset_piece_1"), "my_check")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(passed=True, metadata={"foo": "bar"})
    if AssetKey("multi_asset_piece_2") in context.selected_asset_keys:
        # No check on multi_asset_piece_2
        yield MaterializeResult(asset_key="multi_asset_piece_2")
```

Let's review what we did to accomplish this:

- In the <PyObject section="assets" module="dagster" object="multi_asset" decorator /> decorator:
  - For each <PyObject section="assets" module="dagster" object="AssetSpec" /> in the decorator's `specs` argument, set the `skippable` parameter on <PyObject section="assets" module="dagster" object="AssetSpec" /> to `True`. This allows the asset to be skipped when the multi-asset is materialized.
  - Set the decorator's `can_subset` parameter to `True`, allowing a subset of the computation's assets to be executed
- Use `AssetExecutionContext.selected_asset_keys` to identify which computations to run
- For each asset the multi-asset could create,] explicitly `yield` a <PyObject section="assets" module="dagster" object="MaterializeResult" /> as we don't know in advance which assets will be executed
- Use `AssetExecutionContext.selected_asset_check_keys` to determine which asset check to run. In this example, the `my_check` check will only execute when `multi_asset_piece_1` is materialized.

## APIs in this guide

| Name                                              | Description                                                                                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="asset-checks" module="dagster" object="multi_asset_check" decorator /> | A decorator used to define a set of asset checks that execute together in the same op.               |
| <PyObject section="asset-checks" module="dagster" object="AssetCheckResult" />            | The class returned by asset checks.                                                                                                   |
| <PyObject section="asset-checks" module="dagster" object="AssetCheckSeverity" />          | Defines the severity of a given asset check result.                                                                                   |
| <PyObject section="asset-checks" module="dagster" object="AssetCheckSpec" />              | A class that's passed to asset decorators to define checks that execute in the same op as the asset. |
| <PyObject section="assets" module="dagster" object="multi_asset" decorator />       | A decorator used to define [multi-assets](/guides/build/assets/multi-assets).                                                             |

