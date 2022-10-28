import graphene
from typing_extensions import Protocol

from dagster._core.workspace.context import WorkspaceRequestContext


# Assign this type to `graphene_info` in a resolver to apply typing to `graphene_info.context`.
class HasContext(Protocol):
    @property
    def context(self) -> WorkspaceRequestContext:
        ...


def non_null_list(of_type):
    return graphene.NonNull(graphene.List(graphene.NonNull(of_type)))
