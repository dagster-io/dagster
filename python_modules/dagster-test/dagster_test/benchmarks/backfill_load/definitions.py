"""Code location for the backfill load tests: a chain of daily-partitioned assets.

Sized by environment variables so that the harness can load it as an in-process code location:
BACKFILL_LOAD_NUM_ASSETS, BACKFILL_LOAD_NUM_PARTITIONS, BACKFILL_LOAD_NUM_LARGE_PARTITIONS and
BACKFILL_LOAD_BACKFILL_POLICY (see `backfill_policy`).
"""

import datetime
import os
import warnings

import dagster as dg

START_DATE = datetime.date(2000, 1, 1)
ASSET_PREFIX = "asset"
# A second chain of assets, with BACKFILL_LOAD_NUM_LARGE_PARTITIONS partitions, for mixing large
# backfills with small ones
LARGE_ASSET_PREFIX = "large_asset"


def backfill_policy(name: str) -> dg.BackfillPolicy | None:
    """Parses `single`, `multi<N>` (at most N partitions per run) or `none`."""
    if name == "single":
        return dg.BackfillPolicy.single_run()
    if name.startswith("multi") and name.removeprefix("multi").isdigit():
        return dg.BackfillPolicy.multi_run(int(name.removeprefix("multi")))
    if name == "none":
        return None
    raise ValueError(f"Invalid backfill policy {name!r}: expected single, multi<N> or none")


def _asset_chain(
    prefix: str, num_assets: int, num_partitions: int, policy: dg.BackfillPolicy | None
) -> list[dg.AssetsDefinition]:
    partitions_def = dg.DailyPartitionsDefinition(
        start_date=START_DATE.isoformat(),
        end_date=(START_DATE + datetime.timedelta(days=num_partitions)).isoformat(),
    )

    def make_asset(index: int) -> dg.AssetsDefinition:
        @dg.asset(
            name=f"{prefix}_{index}",
            deps=[f"{prefix}_{index - 1}"] if index > 0 else [],
            partitions_def=partitions_def,
            backfill_policy=policy,
        )
        def _asset() -> None: ...

        return _asset

    return [make_asset(i) for i in range(num_assets)]


@dg.definitions
def defs() -> dg.Definitions:
    num_assets = int(os.getenv("BACKFILL_LOAD_NUM_ASSETS", "10"))
    num_partitions = int(os.getenv("BACKFILL_LOAD_NUM_PARTITIONS", "10000"))
    num_large_partitions = int(os.getenv("BACKFILL_LOAD_NUM_LARGE_PARTITIONS", "0"))
    policy = backfill_policy(os.getenv("BACKFILL_LOAD_BACKFILL_POLICY", "multi1"))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", dg.BetaWarning)  # backfill_policy
        assets = _asset_chain(ASSET_PREFIX, num_assets, num_partitions, policy)
        if num_large_partitions:
            assets += _asset_chain(LARGE_ASSET_PREFIX, num_assets, num_large_partitions, policy)
        return dg.Definitions(assets=assets)
