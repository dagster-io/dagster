import graphene


class Cursor(graphene.ID):
    pass


class PageInfo(graphene.ObjectType):
    lastCursor = graphene.Field(lambda: Cursor)
    hasNextPage = graphene.Field(graphene.Boolean)
    hasPreviousPage = graphene.Field(graphene.Boolean)
    count = graphene.NonNull(graphene.Int)
    totalCount = graphene.NonNull(graphene.Int)
