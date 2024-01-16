import graphene


class GrapheneAssetSelection(graphene.ObjectType):
    assetSelectionString = graphene.String()

    class Meta:
        name = "AssetSelection"
