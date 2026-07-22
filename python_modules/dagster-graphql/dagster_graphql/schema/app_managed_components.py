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


class GrapheneComponent(graphene.ObjectType):
    componentId = graphene.NonNull(graphene.String)
    componentType = graphene.NonNull(graphene.String)
    isAppManaged = graphene.NonNull(graphene.Boolean)
    attributes = graphene.String(
        description="YAML source for the component's attributes (app-managed components only)."
    )
    defsStateKey = graphene.String(
        description="Defs state key for state-backed components (omitted otherwise)."
    )
    defsStateManagementType = graphene.Field(
        "dagster_graphql.schema.external.GrapheneDefsStateManagementType",
        description=(
            "Static state-management type from the component's ``defs_state_config``. "
            "Populated whenever ``defsStateKey`` is — independent of whether a state "
            "record exists yet. Use this to decide whether refresh actions apply."
        ),
    )
    defsStateInfo = graphene.Field(
        "dagster_graphql.schema.external.GrapheneDefsKeyStateInfo",
        description=(
            "Current state version + age for state-backed components. ``null`` for "
            "components that are not state-backed or whose state has not yet been written."
        ),
    )

    class Meta:
        name = "Component"


class GrapheneComponents(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    components = non_null_list(GrapheneComponent)

    class Meta:
        name = "Components"


class GrapheneComponentsOrError(graphene.Union):
    class Meta:
        types = (GrapheneComponents, GraphenePythonError)
        name = "ComponentsOrError"


class GrapheneRefreshComponentStateSuccess(graphene.ObjectType):
    component = graphene.NonNull(GrapheneComponent)

    class Meta:
        name = "RefreshComponentStateSuccess"


class GrapheneRefreshComponentStateAccepted(graphene.ObjectType):
    """Sync-wait elapsed before gRPC reply: refresh is still running. Callers
    should poll ``componentsForLocation`` and watch for the version on
    ``defsStateKey`` to change.
    """

    locationName = graphene.NonNull(graphene.String)
    defsStateKey = graphene.NonNull(graphene.String)

    class Meta:
        name = "RefreshComponentStateAccepted"


class GrapheneRefreshComponentStateError(graphene.ObjectType):
    locationName = graphene.NonNull(graphene.String)
    defsStateKey = graphene.NonNull(graphene.String)
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "RefreshComponentStateError"


class GrapheneRefreshComponentStateResult(graphene.Union):
    class Meta:
        types = (
            GrapheneRefreshComponentStateSuccess,
            GrapheneRefreshComponentStateAccepted,
            GrapheneRefreshComponentStateError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "RefreshComponentStateResult"


types = [
    GrapheneAppManagedComponent,
    GrapheneAppManagedComponents,
    GrapheneAppManagedComponentsOrError,
    GrapheneSetAppManagedComponentSuccess,
    GrapheneSetAppManagedComponentResult,
    GrapheneDeleteAppManagedComponentSuccess,
    GrapheneDeleteAppManagedComponentResult,
    GrapheneComponent,
    GrapheneComponents,
    GrapheneComponentsOrError,
    GrapheneRefreshComponentStateSuccess,
    GrapheneRefreshComponentStateAccepted,
    GrapheneRefreshComponentStateError,
    GrapheneRefreshComponentStateResult,
]
