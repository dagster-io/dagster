import graphene

from .util import non_null_list


class GrapheneAssetKey(graphene.ObjectType):
    path = non_null_list(graphene.String)

    class Meta:
        name = "AssetKey"
