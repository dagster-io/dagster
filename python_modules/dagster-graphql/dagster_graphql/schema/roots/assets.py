import graphene

from ..errors import GrapheneAssetNotFoundError, GraphenePythonError
from ..pipelines.pipeline import GrapheneMaterializedKey
from ..util import non_null_list


class GrapheneMaterializedKeysConnection(graphene.ObjectType):
    nodes = non_null_list(GrapheneMaterializedKey)

    class Meta:
        name = "MaterializedKeysConnection"


class GrapheneMaterializedKeysOrError(graphene.Union):
    class Meta:
        types = (GrapheneMaterializedKeysConnection, GraphenePythonError)
        name = "MaterializedKeysOrError"


class GrapheneMaterializedKeyOrError(graphene.Union):
    class Meta:
        types = (GrapheneMaterializedKey, GrapheneAssetNotFoundError)
        name = "MaterializedKeyOrError"
