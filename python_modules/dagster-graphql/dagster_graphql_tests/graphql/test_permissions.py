from unittest.mock import Mock

import pytest
from dagster import check
from dagster_graphql.implementation.utils import UserFacingGraphQLError, check_permission


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


@pytest.fixture(name="fake_graphene_info")
def fake_graphene_info_fixture():
    context = Mock()

    def fake_has_permission(permission):
        permission_map = {
            "fake_permission": True,
            "fake_other_permission": False,
        }
        check.invariant(permission in permission_map, "Permission does not exist in map")
        return permission_map[permission]

    context.has_permission = Mock(side_effect=fake_has_permission)

    graphene_info = Mock()
    graphene_info.context = context

    return graphene_info


def test_check_permission_has_permission(fake_graphene_info):
    mutation = FakeMutation()
    mutation.mutate(fake_graphene_info)


def test_check_permission_does_not_have_permission(fake_graphene_info):
    mutation = FakeOtherPermissionMutation()
    with pytest.raises(UserFacingGraphQLError, match="GrapheneUnauthorizedError"):
        mutation.mutate(fake_graphene_info)


def test_check_permission_permission_does_not_exist(fake_graphene_info):
    mutation = FakeMissingPermissionMutation()
    with pytest.raises(check.CheckError):
        mutation.mutate(fake_graphene_info)
