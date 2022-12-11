from typing import cast

import graphene
from dagster._core.workspace.context import WorkspaceRequestContext
from typing_extensions import Protocol

class ResolveInfo(graphene.ResolveInfo):
    @property
    def context(self) -> WorkspaceRequestContext:
        return cast(WorkspaceRequestContext, super().context)


def non_null_list(of_type):
    return graphene.NonNull(graphene.List(graphene.NonNull(of_type)))
