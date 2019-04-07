from dagster_graphql import dauphin


class DauphinCursor(dauphin.ID, dauphin.Scalar):
    class Meta:
        name = 'Cursor'


class DauphinPageInfo(dauphin.ObjectType):
    class Meta:
        name = 'PageInfo'

    lastCursor = dauphin.Field('Cursor')
    hasNextPage = dauphin.Field(dauphin.Boolean)
    hasPreviousPage = dauphin.Field(dauphin.Boolean)
    count = dauphin.NonNull(dauphin.Int)
    totalCount = dauphin.NonNull(dauphin.Int)
