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
    todo: add more docs.
    """

    def __new__(cls, max_partitions_per_run: Optional[int] = 1):
        return super(BackfillPolicy, cls).__new__(
            cls,
            max_partitions_per_run=max_partitions_per_run,
        )

    @public
    @staticmethod
    def single_run() -> "BackfillPolicy":
        """Constructs an single_run BackfillPolicy."""
        return BackfillPolicy(max_partitions_per_run=None)

    @public
    @staticmethod
    def multi_run(max_partitions_per_run: int = 1) -> "BackfillPolicy":
        """Constructs a multi_run AutoMaterializePolicy.

        Args:
            max_partitions_per_run (Optional[int]): The maximum number of partitions in a single run. Defaults to 1.
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
