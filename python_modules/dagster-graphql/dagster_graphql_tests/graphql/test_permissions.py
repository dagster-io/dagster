from unittest.mock import Mock

import dagster._check as check
import pytest
from dagster._core.workspace.permissions import (
    EDITOR_PERMISSIONS,
    VIEWER_PERMISSIONS,
    Permissions,
    get_location_scoped_user_permissions,
)
from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission,
    assert_permission_for_location,
    check_permission,
    require_permission_check,
)
from dagster_graphql.schema.util import ResolveInfo
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    NonLaunchableGraphQLContextTestMatrix,
)

PERMISSIONS_QUERY = """
    query PermissionsQuery {
      permissions {
        permission
        value
        disabledReason
      }
    }
"""

WORKSPACE_PERMISSIONS_QUERY = """
query WorkspacePermissionsQuery {
  # faster loading option due to avoiding full workspace load
  locationStatusesOrError {
    __typename
    ... on WorkspaceLocationStatusEntries {
      entries {
        permissions {
          permission
          value
          disabledReason
        }
      }
    }
  }
  workspaceOrError {
    ... on Workspace {
      locationEntries {
        permissions {
          permission
          value
          disabledReason
        }
      }
    }
  }
}
"""


class FakeMutation:
    @check_permission("fake_permission")
    def mutate(self, graphene_info: ResolveInfo, **_kwargs):
        pass


class FakeOtherPermissionMutation:
    @check_permission("fake_other_permission")
    def mutate(self, graphene_info: ResolveInfo, **_kwargs):
        pass


class FakeMissingPermissionMutation:
    @check_permission("fake_missing_permission")
    def mutate(self, graphene_info: ResolveInfo, **_kwargs):
        pass


class FakeEnumPermissionMutation:
    @check_permission(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(self, graphene_info: ResolveInfo, **_kwargs):
        pass


class FakeOtherEnumPermissionMutation:
    @check_permission(Permissions.LAUNCH_PIPELINE_REEXECUTION)
    def mutate(self, graphene_info: ResolveInfo, **_kwargs):
        pass


class FakeMissingEnumPermissionMutation:
    @check_permission(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info: ResolveInfo, **_kwargs):
        pass


class EndpointWithRequiredPermissionCheck:
    @require_permission_check(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(self, graphene_info, **_kwargs):
        assert_permission(graphene_info, Permissions.LAUNCH_PIPELINE_EXECUTION)


class EndpointMissingRequiredPermissionCheck:
    @require_permission_check(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **_kwargs):
        pass


class FakeEnumLocationPermissionMutation:
    @require_permission_check(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(self, graphene_info, **kwargs):
        location_name = kwargs["locationName"]
        assert_permission_for_location(
            graphene_info, Permissions.LAUNCH_PIPELINE_EXECUTION, location_name
        )


@pytest.fixture(name="fake_graphene_info")
def fake_graphene_info_fixture():
    context = Mock()
    _did_check = {}

    def fake_has_permission(permission):
        permission_map = {
            "fake_permission": True,
            "fake_other_permission": False,
            Permissions.LAUNCH_PIPELINE_EXECUTION: True,
            Permissions.LAUNCH_PIPELINE_REEXECUTION: False,
        }
        check.invariant(permission in permission_map, "Permission does not exist in map")
        _did_check[permission] = True
        return permission_map[permission]

    context.has_permission = Mock(side_effect=fake_has_permission)

    def fake_has_permission_for_location(permission, location_name):
        _did_check[permission] = True
        return location_name == "has_location_permission"

    def fake_was_permission_checked(_permission):
        return _did_check.get(_permission) or False

    context.has_permission_for_location = Mock(side_effect=fake_has_permission_for_location)

    context.was_permission_checked = Mock(side_effect=fake_was_permission_checked)

    graphene_info = Mock()
    graphene_info.context = context

    yield graphene_info


def test_check_location_mutation(fake_graphene_info):
    # Fails per-location check
    mutation = FakeEnumLocationPermissionMutation()
    mutation.mutate(fake_graphene_info, locationName="has_location_permission")

    with pytest.raises(UserFacingGraphQLError, match="GrapheneUnauthorizedError"):
        mutation.mutate(fake_graphene_info, locationName="no_location_permission")


def test_require_permission_check_succeeds(fake_graphene_info):
    # Fails per-location check
    mutation = EndpointWithRequiredPermissionCheck()
    mutation.mutate(fake_graphene_info)


def test_require_permission_check_missing(fake_graphene_info):
    # Fails per-location check
    mutation = EndpointMissingRequiredPermissionCheck()
    with pytest.raises(
        Exception, match="Permission launch_partition_backfill was never checked during the request"
    ):
        mutation.mutate(fake_graphene_info)


@pytest.mark.parametrize("mutation", [FakeMutation(), FakeEnumPermissionMutation()])
def test_check_permission_has_permission(fake_graphene_info, mutation):
    mutation.mutate(fake_graphene_info)


@pytest.mark.parametrize(
    "mutation", [FakeOtherPermissionMutation(), FakeOtherEnumPermissionMutation()]
)
def test_check_permission_does_not_have_permission(fake_graphene_info, mutation):
    with pytest.raises(UserFacingGraphQLError, match="GrapheneUnauthorizedError"):
        mutation.mutate(fake_graphene_info)


@pytest.mark.parametrize(
    "mutation", [FakeMissingPermissionMutation(), FakeMissingEnumPermissionMutation()]
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

        for permission in result.data["permissions"]:
            if not permission["value"]:
                assert permission["disabledReason"] == "Disabled by your administrator"
            else:
                assert not permission.get("disabledReason")

    def test_truthy_permission_result(self, graphql_context):
        permissions = graphql_context.permissions
        permission_result = next(iter(permissions.values()))

        with pytest.raises(
            Exception,
            match=(
                "Don't check a PermissionResult for truthiness - check the `enabled` property"
                " instead"
            ),
        ):
            if permission_result:
                pass

        permission_result.enabled  # noqa: B018


class TestWorkspacePermissionsQuery(NonLaunchableGraphQLContextTestMatrix):
    def test_workspace_permissions_query(self, graphql_context):
        result = execute_dagster_graphql(graphql_context, WORKSPACE_PERMISSIONS_QUERY)
        assert result.data

        assert result.data["workspaceOrError"]["locationEntries"]
        assert result.data["locationStatusesOrError"]["entries"]

        # ensure both old and new ways to fetch work and return same data
        assert (
            result.data["locationStatusesOrError"]["entries"]
            == result.data["workspaceOrError"]["locationEntries"]
        )

        for location in result.data["locationStatusesOrError"]["entries"]:
            permissions_map = {
                permission["permission"]: permission["value"]
                for permission in location["permissions"]
            }

            expected_permissions_map = {
                key: perm.enabled
                for key, perm in get_location_scoped_user_permissions(
                    graphql_context.read_only
                ).items()
            }
            assert permissions_map == expected_permissions_map
