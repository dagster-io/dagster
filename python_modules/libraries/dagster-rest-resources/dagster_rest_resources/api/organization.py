from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from typing_extensions import assert_never

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.organization import DgApiOrganizationSettings


@dataclass(frozen=True)
class DgApiOrganizationApi:
    _client: IGraphQLClient

    def get_organization_settings(self) -> DgApiOrganizationSettings:

        result = self._client.get_organization_settings().organization_settings
        if result is None:
            return DgApiOrganizationSettings(settings={})

        return DgApiOrganizationSettings(settings=result.settings or {})

    def update_organization_settings(
        self,
        settings: Mapping[str, Any],
    ) -> "DgApiOrganizationSettings":
        from dagster_rest_resources.__generated__.input_types import OrganizationSettingsInput

        result = self._client.update_organization_settings(
            OrganizationSettingsInput(settings=settings)
        ).set_organization_settings

        match result.typename__:
            case "OrganizationSettings":
                return DgApiOrganizationSettings(settings=result.settings or {})  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(
                    f"Error setting organization settings: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(
                    f"Error setting organization settings: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case _ as unreachable:
                assert_never(unreachable)
