from typing import cast

import graphene
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.workspace.context import WorkspaceRequestContext


class ResolveInfo(graphene.ResolveInfo):
    @property
    def context(self) -> WorkspaceRequestContext:
        return cast(WorkspaceRequestContext, super().context)


def non_null_list(of_type):
    return graphene.NonNull(graphene.List(graphene.NonNull(of_type)))


def get_compute_log_manager(graphene_info: ResolveInfo) -> CapturedLogManager:
    assert isinstance(graphene_info.context.instance.compute_log_manager, CapturedLogManager)
    return graphene_info.context.instance.compute_log_manager
