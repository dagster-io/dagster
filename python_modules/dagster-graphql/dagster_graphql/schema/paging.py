import graphene


class GrapheneCursor(graphene.BigInt, graphene.Scalar):
    class Meta:
        name = "Cursor"
