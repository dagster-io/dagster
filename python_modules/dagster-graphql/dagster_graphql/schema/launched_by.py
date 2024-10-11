import graphene


class GrapheneLaunchedBy(graphene.ObjectType):
    kind = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    def __init__(self, kind: str, value: str):
        self.kind = kind
        self.value = value
