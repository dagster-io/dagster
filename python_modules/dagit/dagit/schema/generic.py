from dagit.schema import dauphin


class Cursor(dauphin.ID, dauphin.Scalar):
    pass


class PageInfo(dauphin.ObjectType):
    lastCursor = dauphin.Field('Cursor')
    hasNextPage = dauphin.Field(dauphin.Boolean)
    hasPreviousPage = dauphin.Field(dauphin.Boolean)
    count = dauphin.NonNull(dauphin.Int)
    totalCount = dauphin.NonNull(dauphin.Int)
