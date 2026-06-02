from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.get_organization_settings import (
    GetOrganizationSettings,
    GetOrganizationSettingsOrganizationSettings,
)
from dagster_rest_resources.__generated__.update_organization_settings import (
    UpdateOrganizationSettings,
    UpdateOrganizationSettingsSetOrganizationSettingsOrganizationSettings,
    UpdateOrganizationSettingsSetOrganizationSettingsPythonError,
    UpdateOrganizationSettingsSetOrganizationSettingsUnauthorizedError,
)
from dagster_rest_resources.api.organization import DgApiOrganizationApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


class TestGetOrganizationSettings:
    def test_returns_settings_from_response(self):
        client = Mock(spec=IGraphQLClient)
        client.get_organization_settings.return_value = GetOrganizationSettings(
            organizationSettings=GetOrganizationSettingsOrganizationSettings(
                settings={"sso_default_role": "VIEWER"}
            )
        )
        result = DgApiOrganizationApi(_client=client).get_organization_settings()

        assert result.settings == {"sso_default_role": "VIEWER"}

    def test_returns_empty_settings_when_none(self):
        client = Mock(spec=IGraphQLClient)
        client.get_organization_settings.return_value = GetOrganizationSettings(
            organizationSettings=None
        )
        result = DgApiOrganizationApi(_client=client).get_organization_settings()

        assert result.settings == {}


class TestUpdateOrganizationSettings:
    def test_success_returns_settings(self):
        client = Mock(spec=IGraphQLClient)
        client.update_organization_settings.return_value = UpdateOrganizationSettings(
            setOrganizationSettings=UpdateOrganizationSettingsSetOrganizationSettingsOrganizationSettings(
                __typename="OrganizationSettings", settings={"sso_default_role": "EDITOR"}
            )
        )

        result = DgApiOrganizationApi(_client=client).update_organization_settings(
            {"sso_default_role": "EDITOR"}
        )

        assert result.settings == {"sso_default_role": "EDITOR"}

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.update_organization_settings.return_value = UpdateOrganizationSettings(
            setOrganizationSettings=UpdateOrganizationSettingsSetOrganizationSettingsUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(
            DagsterPlusUnauthorizedError, match="Error setting organization settings"
        ):
            DgApiOrganizationApi(_client=client).update_organization_settings({})

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.update_organization_settings.return_value = UpdateOrganizationSettings(
            setOrganizationSettings=UpdateOrganizationSettingsSetOrganizationSettingsPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error setting organization settings"):
            DgApiOrganizationApi(_client=client).update_organization_settings({})
