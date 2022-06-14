import graphene

from .util import non_null_list


class GrapheneAssetKey(graphene.ObjectType):
    path = non_null_list(graphene.String)

    class Meta:
        name = "AssetKey"


class GrapheneAssetLineageInfo(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    partitions = non_null_list(graphene.String)

    class Meta:
        name = "AssetLineageInfo"
