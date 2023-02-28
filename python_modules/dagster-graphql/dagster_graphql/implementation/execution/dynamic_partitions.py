from typing import TYPE_CHECKING

from dagster._core.workspace.permissions import Permissions

from dagster_graphql.schema.errors import GrapheneDuplicateDynamicPartitionError

from ..utils import UserFacingGraphQLError, assert_permission, capture_error

if TYPE_CHECKING:
    from ...schema.partition_sets import GrapheneAddDynamicPartitionSuccess


@capture_error
def add_dynamic_partition(
    graphene_info, partitions_def_name: str, partition_key: str
) -> "GrapheneAddDynamicPartitionSuccess":
    from ...schema.partition_sets import GrapheneAddDynamicPartitionSuccess

    assert_permission(graphene_info, Permissions.EDIT_DYNAMIC_PARTITIONS)

    if graphene_info.context.instance.has_dynamic_partition(partitions_def_name, partition_key):
        raise UserFacingGraphQLError(
            GrapheneDuplicateDynamicPartitionError(partitions_def_name, partition_key)
        )

    graphene_info.context.instance.add_dynamic_partitions(partitions_def_name, [partition_key])
    return GrapheneAddDynamicPartitionSuccess(
        partitionsDefName=partitions_def_name, partitionKey=partition_key
    )
