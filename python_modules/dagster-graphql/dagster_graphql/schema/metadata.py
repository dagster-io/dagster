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
        name = "EventMetadataEntry"

class GraphenePathMetadataEntry(graphene.ObjectType):
    path = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventPathMetadataEntry"


class GrapheneTableMetadataEntry(graphene.ObjectType):
    table = graphene.NonNull(GrapheneTable)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventTableMetadataEntry"


class GrapheneTableSchemaMetadataEntry(graphene.ObjectType):

    schema = graphene.NonNull(GrapheneTableSchema)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventTableSchemaMetadataEntry"


class GrapheneJsonMetadataEntry(graphene.ObjectType):
    jsonString = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventJsonMetadataEntry"


class GrapheneTextMetadataEntry(graphene.ObjectType):
    text = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventTextMetadataEntry"


class GrapheneUrlMetadataEntry(graphene.ObjectType):
    url = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventUrlMetadataEntry"


class GrapheneMarkdownMetadataEntry(graphene.ObjectType):
    md_str = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventMarkdownMetadataEntry"


class GraphenePythonArtifactMetadataEntry(graphene.ObjectType):
    module = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventPythonArtifactMetadataEntry"


class GrapheneFloatMetadataEntry(graphene.ObjectType):
    floatValue = graphene.Field(graphene.Float)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventFloatMetadataEntry"


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
        name = "EventIntMetadataEntry"


class GraphenePipelineRunMetadataEntry(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventPipelineRunMetadataEntry"


class GrapheneAssetMetadataEntry(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        interfaces = (GrapheneMetadataEntry,)
        name = "EventAssetMetadataEntry"

def types():
    return [
        GrapheneMetadataEntry,
        GrapheneTableSchemaMetadataEntry,
        GrapheneTableMetadataEntry,
        GrapheneFloatMetadataEntry,
        GrapheneIntMetadataEntry,
        GrapheneJsonMetadataEntry,
        GrapheneMarkdownMetadataEntry,
        GrapheneMetadataItemDefinition,
        GraphenePathMetadataEntry,
        GraphenePythonArtifactMetadataEntry,
        GrapheneTextMetadataEntry,
        GrapheneUrlMetadataEntry,
        GraphenePipelineRunMetadataEntry,
        GrapheneAssetMetadataEntry,
    ]