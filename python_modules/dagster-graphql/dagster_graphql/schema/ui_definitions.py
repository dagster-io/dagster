import graphene

from dagster_graphql.schema.errors import GraphenePythonError, GrapheneUnauthorizedError
from dagster_graphql.schema.util import non_null_list


class GrapheneUIComponent(graphene.ObjectType):
    """A single UI-defined component, persisted in defs state storage.

    ``attributes`` is the YAML source for the component's attributes block,
    stored verbatim so the editing UI can round-trip user input.
    """

    componentId = graphene.NonNull(graphene.String)
    componentType = graphene.NonNull(graphene.String)
    attributes = graphene.NonNull(graphene.String)

    class Meta:
        name = "UIComponent"


class GrapheneUIComponents(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    components = non_null_list(GrapheneUIComponent)

    class Meta:
        name = "UIComponents"


class GrapheneUIComponentsOrError(graphene.Union):
    class Meta:
        types = (GrapheneUIComponents, GraphenePythonError)
        name = "UIComponentsOrError"


class GrapheneSetUIComponentSuccess(graphene.ObjectType):
    component = graphene.NonNull(GrapheneUIComponent)

    class Meta:
        name = "SetUIComponentSuccess"


class GrapheneSetUIComponentResult(graphene.Union):
    class Meta:
        types = (
            GrapheneSetUIComponentSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "SetUIComponentResult"


class GrapheneDeleteUIComponentSuccess(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    componentId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeleteUIComponentSuccess"


class GrapheneDeleteUIComponentResult(graphene.Union):
    class Meta:
        types = (
            GrapheneDeleteUIComponentSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "DeleteUIComponentResult"


types = [
    GrapheneUIComponent,
    GrapheneUIComponents,
    GrapheneUIComponentsOrError,
    GrapheneSetUIComponentSuccess,
    GrapheneSetUIComponentResult,
    GrapheneDeleteUIComponentSuccess,
    GrapheneDeleteUIComponentResult,
]
