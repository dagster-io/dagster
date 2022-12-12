from typing import cast

import graphene
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.workspace.context import WorkspaceRequestContext
from typing_extensions import Protocol


# Assign this type to `graphene_info` in a resolver to apply typing to `graphene_info.context`.
class HasContext(Protocol):
    @property
    def context(self) -> WorkspaceRequestContext:
        ...


def non_null_list(of_type):
    return graphene.NonNull(graphene.List(graphene.NonNull(of_type)))


# Type-ignore because `get_log_data` returns a `ComputeLogManager` but in practice this is
# always also an instance of `CapturedLogManager`, which defines the APIs that we access in
# dagster-graphql. Probably `ComputeLogManager` should subclass `CapturedLogManager`-- this is a
# temporary workaround to satisfy type-checking.
def get_compute_log_manager(graphene_info: HasContext) -> CapturedLogManager:
    return cast(CapturedLogManager, graphene_info.context.instance.compute_log_manager)
