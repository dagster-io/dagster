"""Code location endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.code_location import (
    add_code_location_via_graphql,
    delete_code_location_via_graphql,
    list_code_locations_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.code_location import (
        DgApiAddCodeLocationResult,
        DgApiCodeLocationDocument,
        DgApiCodeLocationList,
        DgApiDeleteCodeLocationResult,
    )


@dataclass(frozen=True)
class DgApiCodeLocationApi:
    client: IGraphQLClient

    def add_code_location(
        self, document: "DgApiCodeLocationDocument"
    ) -> "DgApiAddCodeLocationResult":
        return add_code_location_via_graphql(self.client, document)

    def list_code_locations(self) -> "DgApiCodeLocationList":
        return list_code_locations_via_graphql(self.client)

    def delete_code_location(self, location_name: str) -> "DgApiDeleteCodeLocationResult":
        return delete_code_location_via_graphql(self.client, location_name)
