import graphene
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import AssetJobKey, AssetKey, EntityKey

from dagster_graphql.schema.util import non_null_list


class GrapheneAssetKey(graphene.ObjectType):
    path = non_null_list(graphene.String)

    class Meta:
        name = "AssetKey"

    @staticmethod
    def to_manifest_dict(asset_key: AssetKey) -> dict:
        return {"__typename": "AssetKey", "path": asset_key.path}


class GrapheneAssetCheckHandle(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        name = "AssetCheckhandle"

    def __init__(self, handle: AssetCheckKey):
        super().__init__(name=handle.name, assetKey=GrapheneAssetKey(path=handle.asset_key.path))


class GrapheneAssetJobKey(graphene.ObjectType):
    jobName = graphene.NonNull(graphene.String)

    class Meta:
        name = "AssetJobKey"

    def __init__(self, key: AssetJobKey):
        super().__init__(jobName=key.job_name)


class GrapheneEntityKey(graphene.Union):
    class Meta:
        name = "EntityKey"
        types = (GrapheneAssetKey, GrapheneAssetCheckHandle, GrapheneAssetJobKey)

    @staticmethod
    def from_entity_key(key: EntityKey) -> "GrapheneEntityKey":
        if isinstance(key, AssetKey):
            return GrapheneAssetKey(path=key.path)  # ty: ignore[invalid-return-type]
        elif isinstance(key, AssetJobKey):
            return GrapheneAssetJobKey(key=key)  # ty: ignore[invalid-return-type]
        elif isinstance(key, AssetCheckKey):
            return GrapheneAssetCheckHandle(handle=key)  # ty: ignore[invalid-return-type]
        else:
            raise NotImplementedError(
                f"GraphQL representation not yet supported for {type(key).__name__}"
            )


class GrapheneAssetLineageInfo(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    partitions = non_null_list(graphene.String)

    class Meta:
        name = "AssetLineageInfo"
