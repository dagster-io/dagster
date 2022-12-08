import graphene

from .asset_key import GrapheneAssetKey
from .table import GrapheneTable, GrapheneTableSchema


class GrapheneMetadataItemDefinition(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "MetadataItemDefinition"


class GrapheneMetadataEntry(graphene.Interface):
    label = graphene.NonNull(graphene.String)
    description = graphene.String()

    class Meta:
        name = "MetadataEntry"


class GraphenePathMetadataEntry(graphene.ObjectType):
    path = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "PathMetadataEntry"


class GrapheneNotebookMetadataEntry(graphene.ObjectType):
    path = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "NotebookMetadataEntry"


class GrapheneTableMetadataEntry(graphene.ObjectType):
    table = graphene.NonNull(GrapheneTable)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "TableMetadataEntry"


class GrapheneTableSchemaMetadataEntry(graphene.ObjectType):
    schema = graphene.NonNull(GrapheneTableSchema)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "TableSchemaMetadataEntry"


class GrapheneJsonMetadataEntry(graphene.ObjectType):
    jsonString = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "JsonMetadataEntry"


class GrapheneTextMetadataEntry(graphene.ObjectType):
    text = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "TextMetadataEntry"


class GrapheneUrlMetadataEntry(graphene.ObjectType):
    url = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "UrlMetadataEntry"


class GrapheneMarkdownMetadataEntry(graphene.ObjectType):
    md_str = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "MarkdownMetadataEntry"


class GraphenePythonArtifactMetadataEntry(graphene.ObjectType):
    module = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "PythonArtifactMetadataEntry"


class GrapheneFloatMetadataEntry(graphene.ObjectType):
    floatValue = graphene.Field(graphene.Float)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "FloatMetadataEntry"


class GrapheneIntMetadataEntry(graphene.ObjectType):
    intValue = graphene.Field(
        graphene.Int, description="Nullable to allow graceful degrade on > 32 bit numbers"
    )
    intRepr = graphene.NonNull(
        graphene.String,
        description="String representation of the int to support greater than 32 bit",
    )

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "IntMetadataEntry"


class GrapheneBoolMetadataEntry(graphene.ObjectType):
    boolValue = graphene.Field(graphene.Boolean)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "BoolMetadataEntry"


class GraphenePipelineRunMetadataEntry(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "PipelineRunMetadataEntry"


class GrapheneAssetMetadataEntry(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "AssetMetadataEntry"


class GrapheneNullMetadataEntry(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "NullMetadataEntry"


def types():
    return [
        GrapheneMetadataEntry,
        GrapheneTableSchemaMetadataEntry,
        GrapheneTableMetadataEntry,
        GrapheneFloatMetadataEntry,
        GrapheneIntMetadataEntry,
        GrapheneJsonMetadataEntry,
        GrapheneBoolMetadataEntry,
        GrapheneMarkdownMetadataEntry,
        GrapheneMetadataItemDefinition,
        GraphenePathMetadataEntry,
        GrapheneNotebookMetadataEntry,
        GraphenePythonArtifactMetadataEntry,
        GrapheneTextMetadataEntry,
        GrapheneUrlMetadataEntry,
        GraphenePipelineRunMetadataEntry,
        GrapheneAssetMetadataEntry,
        GrapheneNullMetadataEntry,
    ]
