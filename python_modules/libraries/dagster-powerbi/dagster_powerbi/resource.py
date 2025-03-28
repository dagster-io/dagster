import abc
import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Optional, Union
from urllib.parse import urlencode

import requests
from dagster import (
    ConfigurableResource,
    Definitions,
    _check as check,
)
from dagster._annotations import beta, deprecated, public
from dagster._config.pythonic_config.resource import ResourceDependency
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._core.definitions.events import Failure
from dagster._time import get_current_timestamp
from dagster._utils.cached_method import cached_method
from dagster._utils.security import non_secure_md5_hash_str
from dagster._utils.warnings import deprecation_warning
from pydantic import Field, PrivateAttr

from dagster_powerbi.translator import (
    DagsterPowerBITranslator,
    PowerBIContentData,
    PowerBIContentType,
    PowerBITagSet,
    PowerBITranslatorData,
    PowerBIWorkspaceData,
)

BASE_API_URL = "https://api.powerbi.com/v1.0/myorg"
POWER_BI_RECONSTRUCTION_METADATA_KEY_PREFIX = "__power_bi"

ADMIN_SCAN_TIMEOUT = 60


def _clean_op_name(name: str) -> str:
    """Cleans an input to be a valid Dagster op name."""
    return re.sub(r"[^a-z0-9A-Z]+", "_", name)


def generate_data_source_id(data_source: dict[str, Any]) -> str:
    """Generates a unique ID for a data source based on its properties.
    We use this for cases where the API does not provide a unique ID for a data source.
    This ID is never surfaced to the user and is only used internally to track dependencies.
    """
    return non_secure_md5_hash_str(json.dumps(data_source, sort_keys=True).encode())


class PowerBICredentials(ConfigurableResource, abc.ABC):
    @property
    def api_token(self) -> str: ...


class PowerBIToken(ConfigurableResource):
    """Authenticates with PowerBI directly using an API access token."""

    api_token: str = Field(..., description="An API access token used to connect to PowerBI.")


MICROSOFT_LOGIN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/token"


class PowerBIServicePrincipal(ConfigurableResource):
    """Authenticates with PowerBI using a service principal."""

    client_id: str = Field(..., description="The application client ID for the service principal.")
    client_secret: str = Field(
        ..., description="A client secret created for the service principal."
    )
    tenant_id: str = Field(
        ..., description="The Entra tenant ID where service principal was created."
    )
    _api_token: Optional[str] = PrivateAttr(default=None)

    def get_api_token(self) -> str:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        login_url = MICROSOFT_LOGIN_URL.format(tenant_id=self.tenant_id)
        response = requests.post(
            url=login_url,
            headers=headers,
            data=(
                "grant_type=client_credentials"
                "&resource=https://analysis.windows.net/powerbi/api"
                f"&client_id={self.client_id}"
                f"&client_secret={self.client_secret}"
            ),
            allow_redirects=True,
        )
        response.raise_for_status()
        out = response.json()
        self._api_token = out["access_token"]
        return out["access_token"]

    @property
    def api_token(self) -> str:
        if not self._api_token:
            return self.get_api_token()
        return self._api_token


class PowerBIWorkspace(ConfigurableResource):
    """Represents a workspace in PowerBI and provides utilities
    to interact with the PowerBI API.
    """

    credentials: ResourceDependency[PowerBICredentials]
    workspace_id: str = Field(..., description="The ID of the PowerBI group to use.")
    refresh_poll_interval: int = Field(
        default=5, description="The interval in seconds to poll for refresh status."
    )
    refresh_timeout: int = Field(
        default=300,
        description="The maximum time in seconds to wait for a refresh to complete.",
    )

    @cached_property
    def _api_token(self) -> str:
        return self.credentials.api_token

    def _fetch(
        self,
        endpoint: str,
        method: str = "GET",
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        group_scoped: bool = True,
    ) -> requests.Response:
        """Fetch JSON data from the PowerBI API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_token}",
        }
        base_url = f"{BASE_API_URL}/groups/{self.workspace_id}" if group_scoped else BASE_API_URL
        url = f"{base_url}/{endpoint}"
        if params:
            url_parameters = urlencode(params) if params else None
            url = f"{url}?{url_parameters}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response

    def _fetch_json(
        self,
        endpoint: str,
        method: str = "GET",
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        group_scoped: bool = True,
    ) -> dict[str, Any]:
        return self._fetch(endpoint, method, json, group_scoped=group_scoped, params=params).json()

    @public
    def trigger_and_poll_refresh(self, dataset_id: str) -> None:
        """Triggers a refresh of a PowerBI dataset and polls until it completes or fails."""
        self.trigger_refresh(dataset_id)
        self.poll_refresh(dataset_id)

    @public
    def trigger_refresh(self, dataset_id: str) -> None:
        """Triggers a refresh of a PowerBI dataset."""
        response = self._fetch(
            method="POST",
            endpoint=f"datasets/{dataset_id}/refreshes",
            json={"notifyOption": "NoNotification"},
            group_scoped=True,
        )
        if response.status_code != 202:
            raise Failure(f"Refresh failed to start: {response.content}")

    @public
    def poll_refresh(self, dataset_id: str) -> None:
        """Polls the refresh status of a PowerBI dataset until it completes or fails."""
        status = None

        start = time.monotonic()
        while status not in ["Completed", "Failed"]:
            if time.monotonic() - start > self.refresh_timeout:
                raise Failure(f"Refresh timed out after {self.refresh_timeout} seconds.")

            last_refresh = self._fetch_json(
                f"datasets/{dataset_id}/refreshes",
                group_scoped=True,
            )["value"][0]
            status = last_refresh["status"]

            time.sleep(self.refresh_poll_interval)

        if status == "Failed":
            error = last_refresh.get("serviceExceptionJson")  # pyright: ignore[reportPossiblyUnboundVariable]
            raise Failure(f"Refresh failed: {error}")

    @cached_method
    def _get_reports(self) -> Mapping[str, Any]:
        """Fetches a list of all PowerBI reports in the workspace."""
        return self._fetch_json("reports")

    @cached_method
    def _get_semantic_models(self) -> Mapping[str, Any]:
        """Fetches a list of all PowerBI semantic models in the workspace."""
        return self._fetch_json("datasets")

    @cached_method
    def _get_semantic_model_sources(self, dataset_id: str) -> Mapping[str, Any]:
        """Fetches a list of all data sources for a given semantic model."""
        return self._fetch_json(f"datasets/{dataset_id}/datasources")

    @cached_method
    def _get_dashboards(self) -> Mapping[str, Any]:
        """Fetches a list of all PowerBI dashboards in the workspace."""
        return self._fetch_json("dashboards")

    @cached_method
    def _get_dashboard_tiles(self, dashboard_id: str) -> Mapping[str, Any]:
        """Fetches a list of all tiles for a given PowerBI dashboard,
        including which reports back each tile.
        """
        return self._fetch_json(f"dashboards/{dashboard_id}/tiles")

    @cached_method
    def _scan(self) -> Mapping[str, Any]:
        submission = self._fetch_json(
            method="POST",
            endpoint="admin/workspaces/getInfo",
            group_scoped=False,
            json={"workspaces": [self.workspace_id]},
            params={
                "lineage": "true",
                "datasourceDetails": "true",
                "datasetSchema": "true",
                "datasetExpressions": "true",
            },
        )
        scan_id = submission["id"]

        now = get_current_timestamp()
        start_time = now

        status = None
        while status != "Succeeded" and now - start_time < ADMIN_SCAN_TIMEOUT:
            scan_details = self._fetch_json(
                endpoint=f"admin/workspaces/scanStatus/{scan_id}", group_scoped=False
            )
            status = scan_details["status"]
            time.sleep(0.1)
            now = get_current_timestamp()

        if status != "Succeeded":
            raise Failure(f"Scan not successful after {ADMIN_SCAN_TIMEOUT} seconds: {scan_details}")  # pyright: ignore[reportPossiblyUnboundVariable]

        return self._fetch_json(
            endpoint=f"admin/workspaces/scanResult/{scan_id}", group_scoped=False
        )

    def _fetch_powerbi_workspace_data(self, use_workspace_scan: bool) -> PowerBIWorkspaceData:
        """Retrieves all Power BI content from the workspace and returns it as a PowerBIWorkspaceData object.
        Future work will cache this data to avoid repeated calls to the Power BI API.

        Args:
            use_workspace_scan (bool): Whether to scan the entire workspace using admin APIs
                at once to get all content.

        Returns:
            PowerBIWorkspaceData: A snapshot of the Power BI workspace's content.
        """
        if use_workspace_scan:
            return self._fetch_powerbi_workspace_data_scan()
        return self._fetch_powerbi_workspace_data_legacy()

    def _fetch_powerbi_workspace_data_scan(self) -> PowerBIWorkspaceData:
        scan_result = self._scan()
        augmented_dashboard_data = scan_result["workspaces"][0]["dashboards"]

        dashboards = [
            PowerBIContentData(content_type=PowerBIContentType.DASHBOARD, properties=data)
            for data in augmented_dashboard_data
        ]

        reports = [
            PowerBIContentData(content_type=PowerBIContentType.REPORT, properties=data)
            for data in scan_result["workspaces"][0]["reports"]
        ]

        semantic_models_data = scan_result["workspaces"][0]["datasets"]

        semantic_models = [
            PowerBIContentData(content_type=PowerBIContentType.SEMANTIC_MODEL, properties=dataset)
            for dataset in semantic_models_data
        ]
        return PowerBIWorkspaceData.from_content_data(
            self.workspace_id, dashboards + reports + semantic_models
        )

    def _fetch_powerbi_workspace_data_legacy(self) -> PowerBIWorkspaceData:
        dashboard_data = self._get_dashboards()["value"]
        augmented_dashboard_data = [
            {**dashboard, "tiles": self._get_dashboard_tiles(dashboard["id"])["value"]}
            for dashboard in dashboard_data
        ]
        dashboards = [
            PowerBIContentData(content_type=PowerBIContentType.DASHBOARD, properties=data)
            for data in augmented_dashboard_data
        ]

        reports = [
            PowerBIContentData(content_type=PowerBIContentType.REPORT, properties=data)
            for data in self._get_reports()["value"]
        ]
        semantic_models_data = self._get_semantic_models()["value"]
        data_sources = []
        for dataset in semantic_models_data:
            dataset_sources = self._get_semantic_model_sources(dataset["id"])["value"]

            dataset_sources_with_id = [
                source
                if "datasourceId" in source
                else {"datasourceId": generate_data_source_id(source), **source}
                for source in dataset_sources
            ]
            dataset["sources"] = [source["datasourceId"] for source in dataset_sources_with_id]
            for data_source in dataset_sources_with_id:
                data_sources.append(
                    PowerBIContentData(
                        content_type=PowerBIContentType.DATA_SOURCE, properties=data_source
                    )
                )
        semantic_models = [
            PowerBIContentData(content_type=PowerBIContentType.SEMANTIC_MODEL, properties=dataset)
            for dataset in semantic_models_data
        ]
        return PowerBIWorkspaceData.from_content_data(
            self.workspace_id,
            dashboards + reports + semantic_models + data_sources,
        )

    @public
    @deprecated(
        breaking_version="1.9.0",
        additional_warn_text="Use dagster_powerbi.load_powerbi_asset_specs instead",
    )
    def build_defs(
        self,
        dagster_powerbi_translator: type[DagsterPowerBITranslator] = DagsterPowerBITranslator,
        enable_refresh_semantic_models: bool = False,
    ) -> Definitions:
        """Returns a Definitions object which will load Power BI content from
        the workspace and translate it into assets, using the provided translator.

        Args:
            context (Optional[DefinitionsLoadContext]): The context to use when loading the definitions.
                If not provided, retrieved contextually.
            dagster_powerbi_translator (Type[DagsterPowerBITranslator]): The translator to use
                to convert Power BI content into AssetSpecs. Defaults to DagsterPowerBITranslator.
            enable_refresh_semantic_models (bool): Whether to enable refreshing semantic models
                by materializing them in Dagster.

        Returns:
            Definitions: A Definitions object which will build and return the Power BI content.
        """
        from dagster_powerbi.assets import build_semantic_model_refresh_asset_definition

        resource_key = f'power_bi_{self.workspace_id.replace("-", "_")}'

        return Definitions(
            assets=[
                build_semantic_model_refresh_asset_definition(resource_key, spec)
                if PowerBITagSet.extract(spec.tags).asset_type == "semantic_model"
                else spec
                for spec in load_powerbi_asset_specs(
                    self, dagster_powerbi_translator(), use_workspace_scan=False
                )
            ],
            resources={resource_key: self},
        )


@beta
def load_powerbi_asset_specs(
    workspace: PowerBIWorkspace,
    dagster_powerbi_translator: Optional[
        Union[DagsterPowerBITranslator, type[DagsterPowerBITranslator]]
    ] = None,
    use_workspace_scan: bool = True,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Power BI content in the workspace.

    Args:
        workspace (PowerBIWorkspace): The Power BI workspace to load assets from.
        dagster_powerbi_translator (Optional[Union[DagsterPowerBITranslator, Type[DagsterPowerBITranslator]]]):
            The translator to use to convert Power BI content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterPowerBITranslator`.
        use_workspace_scan (bool): Whether to scan the entire workspace using admin APIs
            at once to get all content. Defaults to True.

    Returns:
        List[AssetSpec]: The set of assets representing the Power BI content in the workspace.
    """
    if isinstance(dagster_powerbi_translator, type):
        deprecation_warning(
            subject="Support of `dagster_powerbi_translator` as a Type[DagsterPowerBITranslator]",
            breaking_version="1.10",
            additional_warn_text=(
                "Pass an instance of DagsterPowerBITranslator or subclass to `dagster_powerbi_translator` instead."
            ),
        )
        dagster_powerbi_translator = dagster_powerbi_translator()

    with workspace.process_config_and_initialize_cm() as initialized_workspace:
        return check.is_list(
            PowerBIWorkspaceDefsLoader(
                workspace=initialized_workspace,
                translator=dagster_powerbi_translator or DagsterPowerBITranslator(),
                use_workspace_scan=use_workspace_scan,
            )
            .build_defs()
            .assets,
            AssetSpec,
        )


@dataclass
class PowerBIWorkspaceDefsLoader(StateBackedDefinitionsLoader[PowerBIWorkspaceData]):
    workspace: PowerBIWorkspace
    translator: DagsterPowerBITranslator
    use_workspace_scan: bool

    @property
    def defs_key(self) -> str:
        return f"{POWER_BI_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.workspace_id}"

    def fetch_state(self) -> PowerBIWorkspaceData:
        with self.workspace.process_config_and_initialize_cm() as initialized_workspace:
            return initialized_workspace._fetch_powerbi_workspace_data(  # noqa: SLF001
                use_workspace_scan=self.use_workspace_scan
            )

    def defs_from_state(self, state: PowerBIWorkspaceData) -> Definitions:
        all_external_data = [
            *state.dashboards_by_id.values(),
            *state.reports_by_id.values(),
            *state.semantic_models_by_id.values(),
        ]
        all_external_asset_specs = [
            self.translator.get_asset_spec(
                PowerBITranslatorData(
                    content_data=content,
                    workspace_data=state,
                )
            )
            for content in all_external_data
        ]

        return Definitions(assets=[*all_external_asset_specs])
