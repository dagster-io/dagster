from typing import TYPE_CHECKING

from dagster._core.workspace.permissions import Permissions

from ..utils import assert_permission, capture_error

if TYPE_CHECKING:
    from ...schema.partition_sets import GrapheneAddDynamicPartitionSuccess


@capture_error
def add_dynamic_partition(
    graphene_info, partitions_def_name: str, partition_key: str
) -> "GrapheneAddDynamicPartitionSuccess":
    from ...schema.partition_sets import GrapheneAddDynamicPartitionSuccess

    assert_permission(graphene_info, Permissions.ADD_DYNAMIC_PARTITION)
    graphene_info.context.instance.add_dynamic_partitions(partitions_def_name, [partition_key])
    return GrapheneAddDynamicPartitionSuccess(
        partitionsDefName=partitions_def_name, partitionKey=partition_key
    )
