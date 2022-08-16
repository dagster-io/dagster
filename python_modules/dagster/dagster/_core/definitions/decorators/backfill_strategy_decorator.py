from dagster._annotations import experimental

from ..backfill_strategy import BackfillStrategy


@experimental
def backfill_strategy(backfill_strategy_fn):
    return BackfillStrategy(backfill_strategy_fn)
