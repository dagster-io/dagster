from unittest.mock import Mock

import pytest
from dagster import check
from dagster.core.workspace.permissions import EDITOR_PERMISSIONS, VIEWER_PERMISSIONS, Permissions
from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission,
    check_permission,
)
from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import NonLaunchableGraphQLContextTestMatrix

PERMISSIONS_QUERY = """
    query PermissionsQuery {
      permissions {
        permission
        value
      }
    }
"""


class FakeMutation:
    @check_permission("fake_permission")
    def mutate(self, graphene_info, **_kwargs):
        pass


class FakeOtherPermissionMutation:
    @check_permission("fake_other_permission")
    def mutate(self, graphene_info, **_kwargs):
        pass


class FakeMissingPermissionMutation:
    @check_permission("fake_missing_permission")
    def mutate(self, graphene_info, **_kwargs):
        pass


class FakeEnumPermissionMutation:
    @check_permission(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(self, graphene_info, **_kwargs):
        pass


class FakeOtherEnumPermisisonMutation:
    @check_permission(Permissions.LAUNCH_PIPELINE_REEXECUTION)
    def mutate(self, graphene_info, **_kwargs):
        pass


class FakeMissingEnumPermisisonMutation:
    @check_permission(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **_kwargs):
        pass


@pytest.fixture(name="fake_graphene_info")
def fake_graphene_info_fixture():
    context = Mock()

    def fake_has_permission(permission):
        permission_map = {
            "fake_permission": True,
            "fake_other_permission": False,
            Permissions.LAUNCH_PIPELINE_EXECUTION: True,
            Permissions.LAUNCH_PIPELINE_REEXECUTION: False,
        }
        check.invariant(permission in permission_map, "Permission does not exist in map")
        return permission_map[permission]

    context.has_permission = Mock(side_effect=fake_has_permission)

    graphene_info = Mock()
    graphene_info.context = context

    return graphene_info


@pytest.mark.parametrize("mutation", [FakeMutation(), FakeEnumPermissionMutation()])
def test_check_permission_has_permission(fake_graphene_info, mutation):
    mutation.mutate(fake_graphene_info)


@pytest.mark.parametrize(
    "mutation", [FakeOtherPermissionMutation(), FakeOtherEnumPermisisonMutation()]
)
def test_check_permission_does_not_have_permission(fake_graphene_info, mutation):
    with pytest.raises(UserFacingGraphQLError, match="GrapheneUnauthorizedError"):
        mutation.mutate(fake_graphene_info)


@pytest.mark.parametrize(
    "mutation", [FakeMissingPermissionMutation(), FakeMissingEnumPermisisonMutation()]
)
def test_check_permission_permission_does_not_exist(fake_graphene_info, mutation):
    with pytest.raises(check.CheckError):
        mutation.mutate(fake_graphene_info)


@pytest.mark.parametrize("permission", ["fake_permission", Permissions.LAUNCH_PIPELINE_EXECUTION])
def test_assert_permission_has_permission(fake_graphene_info, permission):
    assert_permission(fake_graphene_info, permission)


@pytest.mark.parametrize(
    "permission", ["fake_other_permission", Permissions.LAUNCH_PIPELINE_REEXECUTION]
)
def test_assert_permission_does_not_have_permission(fake_graphene_info, permission):
    with pytest.raises(UserFacingGraphQLError, match="GrapheneUnauthorizedError"):
        assert_permission(fake_graphene_info, permission)


@pytest.mark.parametrize(
    "permission", ["fake_missing_permission", Permissions.LAUNCH_PARTITION_BACKFILL]
)
def test_assert_permission_permission_does_not_exist(fake_graphene_info, permission):
    with pytest.raises(check.CheckError):
        assert_permission(fake_graphene_info, permission)


class TestPermissionsQuery(NonLaunchableGraphQLContextTestMatrix):
    def test_permissions_query(self, graphql_context):
        result = execute_dagster_graphql(graphql_context, PERMISSIONS_QUERY)
        assert result.data

        assert result.data["permissions"]

        permissions_map = {
            permission["permission"]: permission["value"]
            for permission in result.data["permissions"]
        }

        if graphql_context.read_only:
            assert permissions_map == VIEWER_PERMISSIONS
        else:
            assert permissions_map == EDITOR_PERMISSIONS
