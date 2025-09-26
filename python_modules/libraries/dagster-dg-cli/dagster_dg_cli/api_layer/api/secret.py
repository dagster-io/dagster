"""Secret endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.secret import (
    get_secret_via_graphql,
    list_secrets_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.secret import DgApiSecret, DgApiSecretList


@dataclass(frozen=True)
class DgApiSecretApi:
    """Secret API operations."""

    client: IGraphQLClient

    def list_secrets(
        self,
        location_name: Optional[str] = None,
        scope: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> "DgApiSecretList":
        """List secrets with optional filtering.

        Args:
            location_name: Optional filter by code location name
            scope: Optional scope filter ("deployment" or "organization")
            limit: Optional limit on number of results

        Returns:
            DgApiSecretList: List of secrets (values are never included for security)

        Note:
            Secret values are never exposed in list operations for security.
            Use get_secret with include_value=True to retrieve specific values.
        """
        return list_secrets_via_graphql(
            self.client,
            location_name=location_name,
            scope=scope,
            include_values=False,  # Never expose values in list operations
            limit=limit,
        )

    def get_secret(
        self,
        secret_name: str,
        location_name: Optional[str] = None,
        include_value: bool = False,
    ) -> "DgApiSecret":
        """Get a specific secret.

        Args:
            secret_name: Name of the secret to retrieve
            location_name: Optional filter by code location name
            include_value: Whether to include the secret value (default: False for security)

        Returns:
            DgApiSecret: Single secret with optional value

        Raises:
            ValueError: If secret not found
        """
        return get_secret_via_graphql(
            self.client,
            secret_name=secret_name,
            location_name=location_name,
            include_value=include_value,
        )
