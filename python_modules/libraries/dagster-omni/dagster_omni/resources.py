import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from dagster import (
    AssetSpec,
    ConfigurableResource,
    Definitions,
    _check as check,
    get_dagster_logger,
)
from dagster._annotations import beta
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr

from dagster_omni.translator import (
    DagsterOmniTranslator,
    OmniContentData,
    OmniContentType,
    OmniTranslatorData,
    OmniWorkspaceData,
)

DEFAULT_POLL_INTERVAL_SECONDS = 10
DEFAULT_POLL_TIMEOUT = 600
OMNI_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-omni/reconstruction_metadata"


@beta
class OmniClient:
    """Client for interacting with the Omni Analytics API."""

    def __init__(self, workspace_url: str, api_key: str):
        self.workspace_url = workspace_url.rstrip("/")
        self.api_key = api_key
        self.base_url = urljoin(self.workspace_url, "/api")
        self._logger = get_dagster_logger()

    @cached_method
    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """Make a request to the Omni API."""
        url = self.base_url + endpoint

        response = requests.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            params=params,
            json=json_data,
            timeout=timeout,
        )
        response.raise_for_status()
        return response

    def get_models(self) -> list[dict[str, Any]]:
        """Fetch all models from the workspace."""
        self._logger.info("Fetching models from Omni workspace")

        response = self._make_request("GET", "/v1/models")
        data = response.json()
        models = data.get("models", [])

        self._logger.info(f"Fetched {len(models)} models")
        return models

    def get_model(self, model_id: str) -> dict[str, Any]:
        """Fetch details for a specific model."""
        response = self._make_request("GET", f"/v1/models/{model_id}")
        return response.json()

    def validate_model(self, model_id: str) -> dict[str, Any]:
        """Validate a specific model."""
        response = self._make_request("GET", f"/v1/models/{model_id}/validate")
        return response.json()

    def refresh_model_schema(self, model_id: str) -> dict[str, Any]:
        """Refresh the schema for a specific model."""
        response = self._make_request("POST", f"/v1/models/{model_id}/refresh")
        return response.json()

    def run_query(
        self,
        query_body: dict[str, Any],
        user_id: Optional[str] = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Run a query and return the results.

        Based on: https://docs.omni.co/docs/API/query-api
        Endpoint: POST /api/v1/query/run
        """
        params = {}
        if user_id:
            params["user_id"] = user_id

        response = self._make_request(
            "POST",
            "/v1/query/run",
            params=params,
            json_data=query_body,
            timeout=timeout,
        )
        return response.json()

    def get_documents(self) -> list[dict[str, Any]]:
        """Fetch documents from the workspace using the Documents API.

        Based on: https://docs.omni.co/docs/API/documents
        Endpoint: GET /api/v1/documents
        """
        self._logger.info("Fetching documents from Omni workspace")

        response = self._make_request("GET", "/v1/documents", params={"pageSize": 100})
        data = response.json()
        documents = data.get("records", [])

        print(f"Fetched {len(documents)} documents")
        print(json.dumps(documents, indent=2))
        print("\n\n")
        self._logger.info(f"Fetched {len(documents)} documents")
        return documents

    def get_document_queries(self, document_id: str) -> list[dict[str, Any]]:
        """Fetch queries for a specific document.

        Based on: https://docs.omni.co/docs/API/guides/run-document-queries
        Endpoint: GET /api/v1/documents/:id/queries
        """
        response = self._make_request("GET", f"/v1/documents/{document_id}/queries")
        return response.json()


@beta
class OmniWorkspace(ConfigurableResource):
    """Represents a workspace in Omni Analytics and provides utilities to interact with the Omni API."""

    workspace_url: str = Field(
        ..., description="The URL of your Omni workspace (e.g., https://myorg.omniapp.co)"
    )
    api_key: str = Field(
        ..., description="API key for authenticating with Omni. Created by Organization Admins."
    )
    poll_interval: int = Field(
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        description="Interval in seconds to poll for job completion.",
    )
    poll_timeout: int = Field(
        default=DEFAULT_POLL_TIMEOUT,
        description="Timeout in seconds for polling operations.",
    )

    _client: Optional[OmniClient] = PrivateAttr(default=None)

    @contextmanager
    def get_client(self) -> Iterator[OmniClient]:
        """Get an authenticated Omni client."""
        if not self._client:
            self._client = OmniClient(
                workspace_url=self.workspace_url,
                api_key=self.api_key,
            )
        yield self._client

    @cached_method
    def fetch_omni_workspace_data(self) -> OmniWorkspaceData:
        """Fetch all Omni content from the workspace and return it as OmniWorkspaceData."""
        with self.get_client() as client:
            all_content = []

            # Fetch models
            # models = client.get_models()
            # for model in models:
            #     all_content.append(
            #         OmniContentData(
            #             content_type=OmniContentType.MODEL,
            #             properties=model,
            #         )
            #     )

            # Fetch documents (which represent workbooks/dashboards in Omni)
            documents = client.get_documents()
            for document in documents:
                # Documents in Omni can represent workbooks/dashboards
                all_content.append(
                    OmniContentData(
                        content_type=OmniContentType.WORKBOOK,
                        properties=document,
                    )
                )

                # Fetch queries for each document
                try:
                    document_queries = []  # client.get_document_queries(document.get("identifier", ""))
                    for query in document_queries:
                        # Skip if query is not a dictionary
                        if not isinstance(query, dict):
                            continue

                        # Add document context to query for lineage
                        query_with_context = {
                            **query,
                            "workbook_id": document.get("identifier"),
                            "workbook_name": document.get("name"),
                        }
                        all_content.append(
                            OmniContentData(
                                content_type=OmniContentType.QUERY,
                                properties=query_with_context,
                            )
                        )
                except Exception as e:
                    # Log but don't fail the entire fetch if one document's queries fail
                    logger = get_dagster_logger()
                    logger.warning(
                        f"Failed to fetch queries for document {document.get('identifier', 'unknown')}: {e}"
                    )
                    continue
            print("\n" * 10)
            print(all_content)

            return OmniWorkspaceData.from_content_data(
                workspace_url=self.workspace_url,
                content_data=all_content,
            )

    def get_or_fetch_workspace_data(self) -> OmniWorkspaceData:
        """Get workspace data using the StateBackedDefinitionsLoader for caching."""
        return OmniWorkspaceDefsLoader(
            workspace=self, translator=DagsterOmniTranslator()
        ).get_or_fetch_state()

    @cached_method
    def load_asset_specs(
        self, dagster_omni_translator: Optional[DagsterOmniTranslator] = None
    ) -> Sequence[AssetSpec]:
        """Load asset specs for Omni content in the workspace."""
        translator = dagster_omni_translator or DagsterOmniTranslator()

        with self.process_config_and_initialize_cm() as initialized_workspace:
            return check.is_list(
                OmniWorkspaceDefsLoader(
                    workspace=initialized_workspace,
                    translator=translator,
                )
                .build_defs()
                .assets,
                AssetSpec,
            )

    def execute_query(
        self,
        query_definition: dict[str, Any],
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute a query in the Omni workspace."""
        with self.get_client() as client:
            return client.run_query(
                query_body=query_definition,
                user_id=user_id,
            )


@beta
def load_omni_asset_specs(
    workspace: OmniWorkspace,
    dagster_omni_translator: Optional[DagsterOmniTranslator] = None,
) -> Sequence[AssetSpec]:
    """Load asset specs for Omni content in the workspace.

    Args:
        workspace: The Omni workspace to load assets from.
        dagster_omni_translator: Optional custom translator for converting Omni content to asset specs.

    Returns:
        Sequence of AssetSpecs representing Omni content.
    """
    return workspace.load_asset_specs(dagster_omni_translator=dagster_omni_translator)


@record
class OmniWorkspaceDefsLoader(StateBackedDefinitionsLoader[OmniWorkspaceData]):
    """Definitions loader for Omni workspace data with caching."""

    workspace: OmniWorkspace
    translator: DagsterOmniTranslator

    @property
    def defs_key(self) -> str:
        """Key for caching the definitions."""
        return f"{OMNI_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.workspace_url}"

    def fetch_state(self) -> OmniWorkspaceData:
        """Fetch the current state of the Omni workspace."""
        return self.workspace.fetch_omni_workspace_data()

    def defs_from_state(self, state: OmniWorkspaceData) -> Definitions:
        """Convert workspace state to Dagster definitions."""
        all_content = [
            *state.models_by_id.values(),
            *state.workbooks_by_id.values(),
            *state.queries_by_id.values(),
        ]

        asset_specs = [
            self.translator.get_asset_spec(
                OmniTranslatorData(content_data=content, workspace_data=state)
            )
            for content in all_content
        ]

        return Definitions(assets=asset_specs)
