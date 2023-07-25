from enum import Enum
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import experimental, public


class BackfillPolicyType(Enum):
    SINGLE_RUN = "SINGLE_RUN"
    MULTI_RUN = "MULTI_RUN"


@experimental
class BackfillPolicy(
    NamedTuple(
        "_BackfillPolicy",
        [
            ("max_partitions_per_run", Optional[int]),
        ],
    )
):
    """An BackfillPolicy specifies how Dagster should attempt to backfill an asset.

    There are two main kinds of auto-materialize policies: single run and multi run. And it only applies
    to partitioned assets.

    In essence, an asset with a single run backfill policy will be take a single dagster run to backfill
    all of its partitions at once, if the asset is partitioned.

    An asset with a multi run backfill policy will take multiple dagster runs to backfill all of its partitions.
    Each dagster run will backfill a subset of the partitions, the number of partitions to backfill in each
    dagster run is specified by the `max_partitions_per_run` parameter.

    For example:

    - If an asset has 100 partitions, and the `max_partitions_per_run` is set to 10, then it will
    be backfilled in 10 dagster runs, each dagster run will backfill 10 partitions.

    - If an asset has 100 partitions, and the `max_partitions_per_run` is set to 11, then it will
    be backfilled in 10 dagster runs, the first 9 dagster runs will backfill 11 partitions, and the last one run
    will backfill the remaining 9 partitions.

    For an asset that is not partitioned, backfill policy should not be assigned to it since we can only backfill
    such asset as a whole.

    **Warning:**

    Constructing an BackfillPolicy directly is not recommended as the API is subject to change.
    BackfillPolicy.single_run() and BackfillPolicy.multi_run(max_partitions_per_run=x) are the recommended API.

    """

    def __new__(cls, max_partitions_per_run: Optional[int] = 1):
        return super(BackfillPolicy, cls).__new__(
            cls,
            max_partitions_per_run=max_partitions_per_run,
        )

    @public
    @staticmethod
    def single_run() -> "BackfillPolicy":
        """Creates a BackfillPolicy that executes the entire backfill in a single run."""
        return BackfillPolicy(max_partitions_per_run=None)

    @public
    @staticmethod
    def multi_run(max_partitions_per_run: int = 1) -> "BackfillPolicy":
        """Creates a BackfillPolicy that executes the entire backfill in multiple runs.
        Each run will backfill [max_partitions_per_run] number of partitions.

        Args:
            max_partitions_per_run (Optional[int]): The maximum number of partitions in each run of the
            multiple runs. Defaults to 1.
        """
        return BackfillPolicy(
            max_partitions_per_run=check.int_param(max_partitions_per_run, "max_partitions_per_run")
        )

    @property
    def policy_type(self) -> BackfillPolicyType:
        if self.max_partitions_per_run:
            return BackfillPolicyType.MULTI_RUN
        else:
            return BackfillPolicyType.SINGLE_RUN
