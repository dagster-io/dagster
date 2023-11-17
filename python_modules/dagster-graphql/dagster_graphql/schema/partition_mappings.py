import graphene
from dagster._core.definitions.partition_mapping import PartitionMapping


class GraphenePartitionMapping(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)

    class Meta:
        name = "PartitionMapping"

    def __init__(
        self,
        partition_mapping: PartitionMapping,
    ):
        super().__init__(
            name=type(partition_mapping).__name__,
            description=str(partition_mapping),
        )
