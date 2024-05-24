from typing import TYPE_CHECKING, Sequence

import graphene

from .asset_key import GrapheneAssetKey
from .util import non_null_list

if TYPE_CHECKING:
    from dagster._core.definitions.metadata.table import TableColumnDep


class GrapheneTableConstraints(graphene.ObjectType):
    other = non_null_list(graphene.String)

    class Meta:
        name = "TableConstraints"


class GrapheneTableColumnConstraints(graphene.ObjectType):
    nullable = graphene.NonNull(graphene.Boolean)
    unique = graphene.NonNull(graphene.Boolean)
    other = non_null_list(graphene.String)

    class Meta:
        name = "TableColumnConstraints"


class GrapheneTableColumn(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    type = graphene.NonNull(graphene.String)
    description = graphene.String()
    constraints = graphene.NonNull(GrapheneTableColumnConstraints)

    class Meta:
        name = "TableColumn"


class GrapheneTableSchema(graphene.ObjectType):
    constraints = graphene.Field(GrapheneTableConstraints)
    columns = non_null_list(GrapheneTableColumn)

    class Meta:
        name = "TableSchema"


class GrapheneTable(graphene.ObjectType):
    schema = graphene.NonNull(GrapheneTableSchema)
    records = non_null_list(graphene.String)  # each element is one record serialized as JSON

    class Meta:
        name = "Table"


class GrapheneTableColumnDep(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    columnName = graphene.NonNull(graphene.String)

    class Meta:
        name = "TableColumnDep"

    def __init__(self, column_dep: "TableColumnDep"):
        super().__init__(assetKey=column_dep.asset_key, columnName=column_dep.column_name)


class GrapheneTableColumnLineageEntry(graphene.ObjectType):
    columnName = graphene.NonNull(graphene.String)
    columnDeps = non_null_list(GrapheneTableColumnDep)

    class Meta:
        name = "TableColumnLineageEntry"

    def __init__(self, column_name: str, column_deps: Sequence["TableColumnDep"]):
        super().__init__(
            columnName=column_name,
            columnDeps=[GrapheneTableColumnDep(column_dep) for column_dep in column_deps],
        )


types = [
    GrapheneTable,
    GrapheneTableSchema,
    GrapheneTableColumn,
    GrapheneTableColumnConstraints,
    GrapheneTableConstraints,
    GrapheneTableColumnDep,
    GrapheneTableColumnLineageEntry,
]
