import graphene

from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.table import (
    GrapheneTable,
    GrapheneTableColumnLineageEntry,
    GrapheneTableSchema,
)
from dagster_graphql.schema.util import non_null_list


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


class GrapheneTableColumnLineageMetadataEntry(graphene.ObjectType):
    lineage = non_null_list(GrapheneTableColumnLineageEntry)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "TableColumnLineageMetadataEntry"


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


class GrapheneJobMetadataEntry(graphene.ObjectType):
    jobName = graphene.NonNull(graphene.String)
    repositoryName = graphene.Field(graphene.String)
    locationName = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "JobMetadataEntry"


class GrapheneLocalFileCodeReference(graphene.ObjectType):
    filePath = graphene.NonNull(graphene.String)
    lineNumber = graphene.Int()
    label = graphene.String()

    class Meta:
        name = "LocalFileCodeReference"


class GrapheneUrlCodeReference(graphene.ObjectType):
    url = graphene.NonNull(graphene.String)
    label = graphene.String()

    class Meta:
        name = "UrlCodeReference"


class GrapheneSourceLocation(graphene.Union):
    class Meta:
        types = (GrapheneLocalFileCodeReference, GrapheneUrlCodeReference)
        name = "SourceLocation"


class GrapheneCodeReferencesMetadataEntry(graphene.ObjectType):
    codeReferences = non_null_list(GrapheneSourceLocation)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "CodeReferencesMetadataEntry"


class GrapheneNullMetadataEntry(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "NullMetadataEntry"


class GrapheneTimestampMetadataEntry(graphene.ObjectType):
    timestamp = graphene.NonNull(graphene.Float)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "TimestampMetadataEntry"


class GraphenePoolMetadataEntry(graphene.ObjectType):
    pool = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "PoolMetadataEntry"


def types():
    return [
        GrapheneMetadataEntry,
        GrapheneTableColumnLineageMetadataEntry,
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
        GrapheneJobMetadataEntry,
        GrapheneCodeReferencesMetadataEntry,
        GrapheneNullMetadataEntry,
        GrapheneTimestampMetadataEntry,
        GraphenePoolMetadataEntry,
    ]
