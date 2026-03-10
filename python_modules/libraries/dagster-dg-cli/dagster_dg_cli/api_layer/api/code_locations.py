"""Code location endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_dg_cli.api_layer.graphql_adapter.code_location import delete_code_location_via_graphql
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.code_location import DeleteCodeLocationResult


@dataclass(frozen=True)
class DgApiCodeLocationApi:
    client: IGraphQLClient

    def delete_code_location(self, name: str) -> "DeleteCodeLocationResult":
        return delete_code_location_via_graphql(self.client, name)
