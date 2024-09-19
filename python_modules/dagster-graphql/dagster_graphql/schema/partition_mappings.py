import graphene
from dagster._core.definitions.partition_mapping import PartitionMapping


class GraphenePartitionMapping(graphene.ObjectType):
    className = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)

    class Meta:
        name = "PartitionMapping"

    def __init__(
        self,
        partition_mapping: PartitionMapping,
    ):
        super().__init__(
            className=type(partition_mapping).__name__,
            description=partition_mapping.description,
        )
