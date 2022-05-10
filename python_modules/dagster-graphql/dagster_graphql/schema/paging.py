# pylint: disable=missing-graphene-docstring
import graphene


class GrapheneCursor(graphene.Int, graphene.Scalar):
    class Meta:
        name = "Cursor"
