import graphene
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import AssetKey, EntityKey

from dagster_graphql.schema.util import non_null_list


class GrapheneAssetKey(graphene.ObjectType):
    path = non_null_list(graphene.String)

    class Meta:
        name = "AssetKey"


class GrapheneAssetCheckHandle(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        name = "AssetCheckhandle"

    def __init__(self, handle: AssetCheckKey):
        super().__init__(name=handle.name, assetKey=GrapheneAssetKey(path=handle.asset_key.path))


class GrapheneEntityKey(graphene.Union):
    class Meta:
        name = "EntityKey"
        types = (GrapheneAssetKey, GrapheneAssetCheckHandle)

    @staticmethod
    def from_entity_key(key: EntityKey) -> "GrapheneEntityKey":
        if isinstance(key, AssetKey):
            return GrapheneAssetKey(path=key.path)
        else:
            return GrapheneAssetCheckHandle(handle=key)


class GrapheneAssetLineageInfo(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    partitions = non_null_list(graphene.String)

    class Meta:
        name = "AssetLineageInfo"
