import graphene

from .util import non_null_list


class GrapheneTagType(graphene.Enum):
    USER_PROVIDED = "USER_PROVIDED"
    SYSTEM = "SYSTEM"
    HIDDEN = "HIDDEN"

    class Meta:
        name = "TagType"


class GraphenePipelineTag(graphene.ObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "PipelineTag"

    def __init__(self, key, value):
        super().__init__(key=key, value=value)


class GraphenePipelineTagAndValues(graphene.ObjectType):
    class Meta:
        description = """A run tag and the free-form values that have been associated
        with it so far."""
        name = "PipelineTagAndValues"

    key = graphene.NonNull(graphene.String)
    values = non_null_list(graphene.String)

    def __init__(self, key, values):
        super().__init__(key=key, values=values)
