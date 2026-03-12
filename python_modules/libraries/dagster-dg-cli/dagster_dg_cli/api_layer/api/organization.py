"""Organization endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.organization import (
    get_organization_settings_via_graphql,
    set_organization_settings_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.organization import OrganizationSettings


@dataclass(frozen=True)
class DgApiOrganizationApi:
    client: IGraphQLClient

    def get_organization_settings(self) -> "OrganizationSettings":
        return get_organization_settings_via_graphql(self.client)

    def update_organization_settings(
        self, settings: "OrganizationSettings"
    ) -> "OrganizationSettings":
        return set_organization_settings_via_graphql(self.client, settings.settings)
