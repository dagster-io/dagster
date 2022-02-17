import graphene

from .asset_key import GrapheneAssetKey
from .table import GrapheneTable, GrapheneTableSchema


class GrapheneMetadataItemDefinition(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "MetadataItemDefinition"


class GrapheneEventMetadataEntry(graphene.Interface):
    label = graphene.NonNull(graphene.String)
    description = graphene.String()

    class Meta:
        name = "EventMetadataEntry"


class GrapheneEventPathMetadataEntry(graphene.ObjectType):
    path = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventPathMetadataEntry"


class GrapheneEventTableMetadataEntry(graphene.ObjectType):
    table = graphene.NonNull(GrapheneTable)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventTableMetadataEntry"


class GrapheneEventTableSchemaMetadataEntry(graphene.ObjectType):

    schema = graphene.NonNull(GrapheneTableSchema)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventTableSchemaMetadataEntry"


class GrapheneEventJsonMetadataEntry(graphene.ObjectType):
    jsonString = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventJsonMetadataEntry"


class GrapheneEventTextMetadataEntry(graphene.ObjectType):
    text = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventTextMetadataEntry"


class GrapheneEventUrlMetadataEntry(graphene.ObjectType):
    url = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventUrlMetadataEntry"


class GrapheneEventMarkdownMetadataEntry(graphene.ObjectType):
    md_str = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventMarkdownMetadataEntry"


class GrapheneEventPythonArtifactMetadataEntry(graphene.ObjectType):
    module = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventPythonArtifactMetadataEntry"


class GrapheneEventFloatMetadataEntry(graphene.ObjectType):
    floatValue = graphene.Field(graphene.Float)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventFloatMetadataEntry"


class GrapheneEventIntMetadataEntry(graphene.ObjectType):
    intValue = graphene.Field(
        graphene.Int, description="Nullable to allow graceful degrade on > 32 bit numbers"
    )
    intRepr = graphene.NonNull(
        graphene.String,
        description="String representation of the int to support greater than 32 bit",
    )

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventIntMetadataEntry"


class GrapheneEventPipelineRunMetadataEntry(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventPipelineRunMetadataEntry"


class GrapheneEventAssetMetadataEntry(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventAssetMetadataEntry"


def types():
    return [
        GrapheneEventMetadataEntry,
        GrapheneEventTableSchemaMetadataEntry,
        GrapheneEventTableMetadataEntry,
        GrapheneEventFloatMetadataEntry,
        GrapheneEventIntMetadataEntry,
        GrapheneEventJsonMetadataEntry,
        GrapheneEventMarkdownMetadataEntry,
        GrapheneMetadataItemDefinition,
        GrapheneEventPathMetadataEntry,
        GrapheneEventPythonArtifactMetadataEntry,
        GrapheneEventTextMetadataEntry,
        GrapheneEventUrlMetadataEntry,
        GrapheneEventPipelineRunMetadataEntry,
        GrapheneEventAssetMetadataEntry,
    ]
