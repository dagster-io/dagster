import graphene

from dagster_graphql.schema.errors import GraphenePythonError, GrapheneUnauthorizedError
from dagster_graphql.schema.util import non_null_list


class GrapheneAppManagedComponent(graphene.ObjectType):
    """A single app-managed component, persisted in defs state storage.

    ``attributes`` is the YAML source for the component's attributes block,
    stored verbatim so the editing UI can round-trip user input.
    """

    componentId = graphene.NonNull(graphene.String)
    componentType = graphene.NonNull(graphene.String)
    attributes = graphene.NonNull(graphene.String)

    class Meta:
        name = "AppManagedComponent"


class GrapheneAppManagedComponents(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    components = non_null_list(GrapheneAppManagedComponent)

    class Meta:
        name = "AppManagedComponents"


class GrapheneAppManagedComponentsOrError(graphene.Union):
    class Meta:
        types = (GrapheneAppManagedComponents, GraphenePythonError)
        name = "AppManagedComponentsOrError"


class GrapheneSetAppManagedComponentSuccess(graphene.ObjectType):
    component = graphene.NonNull(GrapheneAppManagedComponent)

    class Meta:
        name = "SetAppManagedComponentSuccess"


class GrapheneSetAppManagedComponentResult(graphene.Union):
    class Meta:
        types = (
            GrapheneSetAppManagedComponentSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "SetAppManagedComponentResult"


class GrapheneDeleteAppManagedComponentSuccess(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    componentId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeleteAppManagedComponentSuccess"


class GrapheneDeleteAppManagedComponentResult(graphene.Union):
    class Meta:
        types = (
            GrapheneDeleteAppManagedComponentSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "DeleteAppManagedComponentResult"


types = [
    GrapheneAppManagedComponent,
    GrapheneAppManagedComponents,
    GrapheneAppManagedComponentsOrError,
    GrapheneSetAppManagedComponentSuccess,
    GrapheneSetAppManagedComponentResult,
    GrapheneDeleteAppManagedComponentSuccess,
    GrapheneDeleteAppManagedComponentResult,
]
