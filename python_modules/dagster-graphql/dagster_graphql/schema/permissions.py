# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check


class GraphenePermission(graphene.ObjectType):
    class Meta:
        "Permission"

    permission = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.Boolean)

    def __init__(self, permission: str, value: bool):
        check.str_param(permission, "permission")
        check.bool_param(value, "value")

        super().__init__(permission=permission, value=value)
