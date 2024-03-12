import graphene

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


class GrapheneTableColumnSpec(graphene.ObjectType):
    columnName = graphene.NonNull(graphene.String)
    tableColumnDeps = non_null_list(GrapheneTableColumnDep)

    class Meta:
        name = "TableColumnSpec"


class GrapheneTableSpec(graphene.ObjectType):
    columnSpecs = graphene.NonNull(GrapheneTableColumnSpec)

    class Meta:
        name = "TableSpec"


types = [
    GrapheneTable,
    GrapheneTableSchema,
    GrapheneTableColumn,
    GrapheneTableColumnConstraints,
    GrapheneTableConstraints,
    GrapheneTableColumnDep,
    GrapheneTableColumnSpec,
    GrapheneTableSpec,
]
