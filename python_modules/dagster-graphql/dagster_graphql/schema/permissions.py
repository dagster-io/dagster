import dagster._check as check
import graphene
from dagster._core.workspace.permissions import PermissionResult


class GraphenePermission(graphene.ObjectType):
    class Meta:
        name = "Permission"

    permission = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.Boolean)
    disabledReason = graphene.Field(graphene.String)

    def __init__(self, permission: str, permission_result: PermissionResult):
        check.str_param(permission, "permission")
        check.inst_param(permission_result, "permission_result", PermissionResult)

        super().__init__(
            permission=permission,
            value=permission_result.enabled,
            disabledReason=permission_result.disabled_reason,
        )
