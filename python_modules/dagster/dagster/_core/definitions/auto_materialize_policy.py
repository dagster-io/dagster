from enum import Enum
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._serdes.serdes import whitelist_for_serdes


class AutoMaterializePolicyType(Enum):
    EAGER = "EAGER"
    LAZY = "LAZY"


@experimental
@whitelist_for_serdes(old_fields={"time_window_partition_scope_minutes": 1e-6})
class AutoMaterializePolicy(
    NamedTuple(
        "_AutoMaterializePolicy",
        [
            ("on_missing", bool),
            ("on_new_parent_data", bool),
            ("for_freshness", bool),
            ("max_materializations_per_minute", Optional[int]),
        ],
    )
):
    """An AutoMaterializePolicy specifies how Dagster should attempt to keep an asset up-to-date.

    There are two main kinds of auto-materialize policies: eager and lazy. In essence, an asset with
    an eager policy will try to immediately materialize after upstream changes, while an asset with
    a lazy policy will only materialize when necessary in order to satisfy the relevant
    FreshnessPolicies.

    For an asset / partition of an asset with an _eager_ policy to be auto-materialized, at least
    one of the following must be true:

    - it is missing
    - it has a freshness policy that requires more up-to-date data
    - any of its descendants have a freshness policy that require more up-to-date data
    - any of its parent assets / partitions have newer data

    For an asset / partition of an asset with a _lazy_ policy to be auto-materialized, at least one
    of the following must be true:

    - it has a freshness policy that requires more up-to-date data
    - any of its descendants have a freshness policy that require more up-to-date data

    If an asset / partition meets the above criteria, then it will be auto-materialized only if none
    of the following are true:

    - any of its parent assets / partitions are missing
    - any of its ancestor assets / partitions have ancestors of their own with newer data

    Lastly, the `max_materializations_per_minute` parameter, which is set to 1 by default,
    rate-limits the number of auto-materializations that can occur for a particular asset within
    a short time interval. This mainly matters for partitioned assets. Its purpose is to provide a
    safeguard against "surprise backfills", where user-error causes auto-materialize to be
    accidentally triggered for large numbers of partitions at once.

    **Warning:**

    Constructing an AutoMaterializePolicy directly is not recommended as the API is subject to change.
    AutoMaterializePolicy.eager() and AutoMaterializePolicy.lazy() are the recommended API.

    """

    def __new__(
        cls,
        on_missing: bool,
        on_new_parent_data: bool,
        for_freshness: bool,
        max_materializations_per_minute: Optional[int] = 1,
    ):
        check.invariant(
            on_new_parent_data or for_freshness,
            "One of on_new_parent_data or for_freshness must be True",
        )
        check.invariant(
            max_materializations_per_minute is None or max_materializations_per_minute > 0,
            (
                "max_materializations_per_minute must be positive. To disable rate-limiting, set it"
                " to None. To disable auto materializing, remove the policy."
            ),
        )

        return super(AutoMaterializePolicy, cls).__new__(
            cls,
            on_missing=on_missing,
            on_new_parent_data=on_new_parent_data,
            for_freshness=for_freshness,
            max_materializations_per_minute=max_materializations_per_minute,
        )

    @public
    @staticmethod
    def eager(max_materializations_per_minute: Optional[int] = 1) -> "AutoMaterializePolicy":
        """Constructs an eager AutoMaterializePolicy.

        Args:
            max_materializations_per_minute (Optional[int]): The maximum number of
                auto-materializations for this asset that may be initiated per minute. If this limit
                is exceeded, the partitions which would have been materialized will be discarded,
                and will require manual materialization in order to be updated. Defaults to 1.
        """
        return AutoMaterializePolicy(
            on_missing=True,
            on_new_parent_data=True,
            for_freshness=True,
            max_materializations_per_minute=check.opt_int_param(
                max_materializations_per_minute, "max_materializations_per_minute"
            ),
        )

    @public
    @staticmethod
    def lazy(max_materializations_per_minute: Optional[int] = 1) -> "AutoMaterializePolicy":
        """Constructs a lazy AutoMaterializePolicy.

        Args:
            max_materializations_per_minute (Optional[int]): The maximum number of
                auto-materializations for this asset that may be initiated per minute. If this limit
                is exceeded, the partitions which would have been materialized will be discarded,
                and will require manual materialization in order to be updated. Defaults to 1.
        """
        return AutoMaterializePolicy(
            on_missing=False,
            on_new_parent_data=False,
            for_freshness=True,
            max_materializations_per_minute=check.opt_int_param(
                max_materializations_per_minute, "max_materializations_per_minute"
            ),
        )

    @property
    def policy_type(self) -> AutoMaterializePolicyType:
        if self.on_new_parent_data is True:
            return AutoMaterializePolicyType.EAGER
        return AutoMaterializePolicyType.LAZY
