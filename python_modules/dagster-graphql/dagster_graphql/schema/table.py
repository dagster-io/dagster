import graphene
from dagster._core.definitions.metadata.table import TableColumnLineage

from .asset_key import GrapheneAssetKey
from .util import non_null_list


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


class GrapheneTableColumnLineageEntry(graphene.ObjectType):
    columnName = graphene.NonNull(graphene.String)
    columnDeps = non_null_list(GrapheneTableColumnDep)

    class Meta:
        name = "TableColumnLineageEntry"


class GrapheneTableColumnLineage(graphene.ObjectType):
    entries = non_null_list(GrapheneTableColumnLineageEntry)

    class Meta:
        name = "TableColumnLineage"

    def __init__(self, column_lineage: TableColumnLineage):
        super().__init__(
            entries=[
                GrapheneTableColumnLineageEntry(
                    column_name,
                    [
                        GrapheneTableColumnDep(column_dep.asset_key, column_dep.column_name)
                        for column_dep in column_deps
                    ],
                )
                for column_name, column_deps in column_lineage.deps_by_column.items()
            ]
        )


types = [
    GrapheneTable,
    GrapheneTableSchema,
    GrapheneTableColumn,
    GrapheneTableColumnConstraints,
    GrapheneTableConstraints,
    GrapheneTableColumnDep,
    GrapheneTableColumnLineageEntry,
    GrapheneTableColumnLineage,
]
