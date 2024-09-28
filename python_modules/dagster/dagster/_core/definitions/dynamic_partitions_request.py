from typing import NamedTuple, Sequence

import dagster._check as check
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
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
        return super(AddDynamicPartitionsRequest, cls).__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
        )


@whitelist_for_serdes
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
        return super(DeleteDynamicPartitionsRequest, cls).__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
        )
