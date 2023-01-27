from typing import Any, cast

import graphene
from dagster._core.workspace.context import WorkspaceRequestContext
from typing_extensions import Protocol, TypeAlias

# Unfortunately Graphene input objects do not play nicely with typing-- we can't type arguments to
# resolvers with `GrapheneMyInputObjectType` and have it work. We use this `InputObject` type as a
# stand-in until a better solution is found.
InputObject: TypeAlias = Any

class ResolveInfo(graphene.ResolveInfo):
    @property
    def context(self) -> WorkspaceRequestContext:
        return cast(WorkspaceRequestContext, super().context)


def non_null_list(of_type):
    return graphene.NonNull(graphene.List(graphene.NonNull(of_type)))
