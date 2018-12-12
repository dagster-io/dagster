from dagit.schema import dauphene


class Cursor(dauphene.ID, dauphene.Scalar):
    pass


class PageInfo(dauphene.ObjectType):
    lastCursor = dauphene.Field('Cursor')
    hasNextPage = dauphene.Field(dauphene.Boolean)
    hasPreviousPage = dauphene.Field(dauphene.Boolean)
    count = dauphene.NonNull(dauphene.Int)
    totalCount = dauphene.NonNull(dauphene.Int)
