"""Code location endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.code_location import (
    add_code_location_via_graphql,
    delete_code_location_via_graphql,
    get_code_location_via_graphql,
    list_code_locations_via_graphql,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.code_location import (
        DgApiAddCodeLocationResult,
        DgApiCodeLocation,
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

    def get_code_location(self, location_name: str) -> "DgApiCodeLocation | None":
        return get_code_location_via_graphql(self.client, location_name)

    def delete_code_location(self, location_name: str) -> "DgApiDeleteCodeLocationResult":
        return delete_code_location_via_graphql(self.client, location_name)
