from collections.abc import Mapping, Sequence
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
            ("partition_key_labels", Mapping[str, str] | None),
        ],
    )
):
    """A request to add partitions to a dynamic partitions definition, to be evaluated by a sensor or schedule."""

    def __new__(
        cls,
        partitions_def_name: str,
        partition_keys: Sequence[str],
        partition_key_labels: Mapping[str, str] | None = None,
    ):
        return super().__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
            partition_key_labels=check.opt_nullable_mapping_param(
                partition_key_labels,
                "partition_key_labels",
                key_type=str,
                value_type=str,
            ),
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
