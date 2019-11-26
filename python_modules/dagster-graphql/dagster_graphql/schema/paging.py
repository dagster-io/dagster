from dagster_graphql import dauphin


class DauphinCursor(dauphin.Int, dauphin.Scalar):
    class Meta(object):
        name = 'Cursor'


class DauphinPageInfo(dauphin.ObjectType):
    class Meta(object):
        name = 'PageInfo'

    lastCursor = dauphin.Field('Cursor')
    hasNextPage = dauphin.Field(dauphin.Boolean)
    hasPreviousPage = dauphin.Field(dauphin.Boolean)
    count = dauphin.NonNull(dauphin.Int)
    totalCount = dauphin.NonNull(dauphin.Int)
