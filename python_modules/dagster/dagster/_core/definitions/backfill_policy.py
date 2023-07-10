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
            ("is_single_run", bool),
            ("max_partitions_per_run", Optional[int]),
        ],
    )
):
    """An BackfillPolicy specifies how Dagster should attempt to backfill an asset.
    todo: add more docs.
    """

    def __new__(
        cls,
        is_single_run: bool = False,
        max_partitions_per_run: Optional[int] = 1,
    ):
        check.invariant(
            (is_single_run and max_partitions_per_run is None)
            or (is_single_run is False and max_partitions_per_run is not None),
            (
                "Single run does not support max_partitions_per_run and non single run requires"
                " max_partitions_per_run"
            ),
        )

        return super(BackfillPolicy, cls).__new__(
            cls,
            is_single_run=is_single_run,
            max_partitions_per_run=max_partitions_per_run,
        )

    @public
    @staticmethod
    def single_run() -> "BackfillPolicy":
        """Constructs an single_run BackfillPolicy."""
        return BackfillPolicy(
            is_single_run=True,
            max_partitions_per_run=None,
        )

    @public
    @staticmethod
    def multi_run(max_partitions_per_run: Optional[int] = 1) -> "BackfillPolicy":
        """Constructs a multi_run AutoMaterializePolicy.

        Args:
            max_partitions_per_run (Optional[int]): The maximum number of partitions in a single run. Defaults to 1.
        """
        return BackfillPolicy(
            is_single_run=False,
            max_partitions_per_run=check.opt_int_param(
                max_partitions_per_run, "max_partitions_per_run"
            ),
        )

    @property
    def policy_type(self) -> BackfillPolicyType:
        if self.is_single_run is True:
            return BackfillPolicyType.SINGLE_RUN
        return BackfillPolicyType.MULTI_RUN
