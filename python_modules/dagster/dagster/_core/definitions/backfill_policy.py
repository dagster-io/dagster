from collections.abc import Iterable
from enum import Enum
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import beta, public
from dagster._serdes import whitelist_for_serdes
from dagster._utils.warnings import disable_dagster_warnings


class BackfillPolicyType(Enum):
    SINGLE_RUN = "SINGLE_RUN"
    MULTI_RUN = "MULTI_RUN"


@beta
@whitelist_for_serdes
class BackfillPolicy(
    NamedTuple(
        "_BackfillPolicy",
        [
            ("max_partitions_per_run", Optional[int]),
        ],
    )
):
    """A BackfillPolicy specifies how Dagster should attempt to backfill a partitioned asset.

    There are two main kinds of backfill policies: single-run and multi-run.

    An asset with a single-run backfill policy will take a single run to backfill all of its
    partitions at once.

    An asset with a multi-run backfill policy will take multiple runs to backfill all of its
    partitions. Each run will backfill a subset of the partitions. The number of partitions to
    backfill in each run is controlled by the `max_partitions_per_run` parameter.

    For example:

    - If an asset has 100 partitions, and the `max_partitions_per_run` is set to 10, then it will
      be backfilled in 10 runs; each run will backfill 10 partitions.

    - If an asset has 100 partitions, and the `max_partitions_per_run` is set to 11, then it will
      be backfilled in 10 runs; the first 9 runs will backfill 11 partitions, and the last one run
      will backfill the remaining 9 partitions.

    **Warning:**

    Constructing an BackfillPolicy directly is not recommended as the API is subject to change.
    BackfillPolicy.single_run() and BackfillPolicy.multi_run(max_partitions_per_run=x) are the
    recommended APIs.
    """

    def __new__(cls, max_partitions_per_run: Optional[int] = 1):
        return super().__new__(
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
            max_partitions_per_run (Optional[int]): The maximum number of partitions in each run of
                the multiple runs. Defaults to 1.
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

    def __str__(self):
        return (
            "BackfillPolicy.single_run()"
            if self.policy_type == BackfillPolicyType.SINGLE_RUN
            else (f"BackfillPolicy.multi_run(max_partitions_per_run={self.max_partitions_per_run})")
        )


# In situations where multiple backfill policies are specified, call this to resolve a canonical
# policy, which is the policy with the minimum max_partitions_per_run.
def resolve_backfill_policy(
    backfill_policies: Iterable[Optional[BackfillPolicy]],
) -> BackfillPolicy:
    policy = next(iter(sorted(backfill_policies, key=_backfill_policy_sort_key)), None)
    with disable_dagster_warnings():
        return policy or BackfillPolicy.multi_run(1)


def _backfill_policy_sort_key(bp: Optional[BackfillPolicy]) -> float:
    if bp is None:  # equivalent to max_partitions_per_run=1
        return 1
    elif bp.max_partitions_per_run is None:
        return float("inf")
    else:
        return bp.max_partitions_per_run
