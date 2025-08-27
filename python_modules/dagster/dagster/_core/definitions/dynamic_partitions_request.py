from collections.abc import Sequence
from typing import NamedTuple

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._annotations import public


@whitelist_for_serdes
@public
class AddDynamicPartitionsRequest(
    NamedTuple(
        "_AddDynamicPartitionsRequest",
        [
            ("partitions_def_name", str),
            ("partition_keys", Sequence[str]),
        ],
    )
):
    """A request to add partitions to a dynamic partitions definition, to be evaluated by a sensor or schedule."""

    def __new__(
        cls,
        partitions_def_name: str,
        partition_keys: Sequence[str],
    ):
        return super().__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
        )


@whitelist_for_serdes
@public
class DeleteDynamicPartitionsRequest(
    NamedTuple(
        "_AddDynamicPartitionsRequest",
        [
            ("partitions_def_name", str),
            ("partition_keys", Sequence[str]),
        ],
    )
):
    """A request to delete partitions to a dynamic partitions definition, to be evaluated by a sensor or schedule."""

    def __new__(
        cls,
        partitions_def_name: str,
        partition_keys: Sequence[str],
    ):
        return super().__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
        )
