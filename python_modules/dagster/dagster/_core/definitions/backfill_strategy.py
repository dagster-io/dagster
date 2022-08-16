from typing import Sequence

from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.execution.context.backfill_strategy import BackfillStrategyContext


class BackfillStrategy:
    """
    Defines how to translate a submitted backfill into a set of runs.
    """
