import re
import time
from typing import Any, Dict, Sequence, Type, cast

import requests
from dagster import (
    AssetsDefinition,
    ConfigurableResource,
    Definitions,
    _check as check,
    external_assets_from_specs,
    multi_asset,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.events import Failure
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils.cached_method import cached_method
from pydantic import Field

from dagster_powerbi.translator import (
    DagsterPowerBITranslator,
    PowerBIContentData,
    PowerBIContentType,
    PowerBIWorkspaceData,
)

BASE_API_URL = "https://api.powerbi.com/v1.0/myorg"


def _clean_op_name(name: str) -> str:
    """Cleans an input to be a valid Dagster op name."""
    return re.sub(r"[^a-z0-9A-Z]+", "_", name)


class PowerBIWorkspace(ConfigurableResource):
    """Represents a workspace in PowerBI and provides utilities
    to interact with the PowerBI API.
    """

    api_token: str = Field(..., description="An API token used to connect to PowerBI.")
    workspace_id: str = Field(..., description="The ID of the PowerBI group to use.")
    refresh_poll_interval: int = Field(
        default=5, description="The interval in seconds to poll for refresh status."
    )
    refresh_timeout: int = Field(
        default=300, description="The maximum time in seconds to wait for a refresh to complete."
    )

    def fetch(
        self, endpoint: str, method: str = "GET", json: Any = None, group_scoped: bool = True
    ) -> requests.Response:
        """Fetch JSON data from the PowerBI API. Raises an exception if the request fails.

        Args:
            endpoint (str): The API endpoint to fetch data from.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        base_url = f"{BASE_API_URL}/groups/{self.workspace_id}" if group_scoped else BASE_API_URL
        response = requests.request(
            method=method,
            url=f"{base_url}/{endpoint}",
            headers=headers,
            json=json,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response

    def fetch_json(
        self, endpoint: str, method: str = "GET", json: Any = None, group_scoped: bool = True
    ) -> Dict[str, Any]:
        return self.fetch(endpoint, method, json, group_scoped=group_scoped).json()

    def trigger_refresh(self, dataset_id: str) -> None:
        """Triggers a refresh of a PowerBI dataset."""
        response = self.fetch(
            method="POST",
            endpoint=f"datasets/{dataset_id}/refreshes",
            json={"notifyOption": "NoNotification"},
            group_scoped=False,
        )
        if response.status_code != 202:
            raise Failure(f"Refresh failed to start: {response.content}")

    def poll_refresh(self, dataset_id: str) -> None:
        """Polls the refresh status of a PowerBI dataset until it completes or fails."""
        status = None

        start = time.monotonic()
        while status not in ["Completed", "Failed"]:
            if time.monotonic() - start > self.refresh_timeout:
                raise Failure(f"Refresh timed out after {self.refresh_timeout} seconds.")

            last_refresh = self.fetch_json(
                f"datasets/{dataset_id}/refreshes",
                group_scoped=False,
            )["value"][0]
            status = last_refresh["status"]

            time.sleep(self.refresh_poll_interval)

        if status == "Failed":
            error = last_refresh.get("serviceExceptionJson")
            raise Failure(f"Refresh failed: {error}")

    @cached_method
    def get_reports(self) -> Dict[str, Any]:
        """Fetches a list of all PowerBI reports in the workspace."""
        return self.fetch_json("reports")

    @cached_method
    def get_semantic_models(self) -> Dict[str, Any]:
        """Fetches a list of all PowerBI semantic models in the workspace."""
        return self.fetch_json("datasets")

    @cached_method
    def get_semantic_model_sources(
        self,
        dataset_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all data sources for a given semantic model."""
        return self.fetch_json(f"datasets/{dataset_id}/datasources")

    @cached_method
    def get_dashboards(self) -> Dict[str, Any]:
        """Fetches a list of all PowerBI dashboards in the workspace."""
        return self.fetch_json("dashboards")

    @cached_method
    def get_dashboard_tiles(
        self,
        dashboard_id: str,
    ) -> Dict[str, Any]:
        """Fetches a list of all tiles for a given PowerBI dashboard,
        including which reports back each tile.
        """
        return self.fetch_json(f"dashboards/{dashboard_id}/tiles")

    def fetch_powerbi_workspace_data(
        self,
    ) -> PowerBIWorkspaceData:
        """Retrieves all Power BI content from the workspace and returns it as a PowerBIWorkspaceData object.
        Future work will cache this data to avoid repeated calls to the Power BI API.

        Returns:
            PowerBIWorkspaceData: A snapshot of the Power BI workspace's content.
        """
        dashboard_data = self.get_dashboards()["value"]
        augmented_dashboard_data = [
            {**dashboard, "tiles": self.get_dashboard_tiles(dashboard["id"])["value"]}
            for dashboard in dashboard_data
        ]
        dashboards = [
            PowerBIContentData(content_type=PowerBIContentType.DASHBOARD, properties=data)
            for data in augmented_dashboard_data
        ]

        reports = [
            PowerBIContentData(content_type=PowerBIContentType.REPORT, properties=data)
            for data in self.get_reports()["value"]
        ]
        semantic_models_data = self.get_semantic_models()["value"]
        data_sources_by_id = {}
        for dataset in semantic_models_data:
            dataset_sources = self.get_semantic_model_sources(dataset["id"])["value"]
            dataset["sources"] = [source["datasourceId"] for source in dataset_sources]
            for data_source in dataset_sources:
                data_sources_by_id[data_source["datasourceId"]] = PowerBIContentData(
                    content_type=PowerBIContentType.DATA_SOURCE, properties=data_source
                )
        semantic_models = [
            PowerBIContentData(content_type=PowerBIContentType.SEMANTIC_MODEL, properties=dataset)
            for dataset in semantic_models_data
        ]
        return PowerBIWorkspaceData.from_content_data(
            self.workspace_id,
            dashboards + reports + semantic_models + list(data_sources_by_id.values()),
        )

    def build_assets(
        self,
        dagster_powerbi_translator: Type[DagsterPowerBITranslator],
        enable_refresh_semantic_models: bool,
    ) -> Sequence[CacheableAssetsDefinition]:
        """Returns a set of CacheableAssetsDefinition which will load Power BI content from
        the workspace and translates it into AssetSpecs, using the provided translator.

        Args:
            dagster_powerbi_translator (Type[DagsterPowerBITranslator]): The translator to use
                to convert Power BI content into AssetSpecs. Defaults to DagsterPowerBITranslator.

        Returns:
            Sequence[CacheableAssetsDefinition]: A list of CacheableAssetsDefinitions which
                will load the Power BI content.
        """
        return [
            PowerBICacheableAssetsDefinition(
                self,
                dagster_powerbi_translator,
                enable_refresh_semantic_models=enable_refresh_semantic_models,
            )
        ]

    def build_defs(
        self,
        dagster_powerbi_translator: Type[DagsterPowerBITranslator] = DagsterPowerBITranslator,
        enable_refresh_semantic_models: bool = False,
    ) -> Definitions:
        """Returns a Definitions object which will load Power BI content from
        the workspace and translate it into assets, using the provided translator.

        Args:
            dagster_powerbi_translator (Type[DagsterPowerBITranslator]): The translator to use
                to convert Power BI content into AssetSpecs. Defaults to DagsterPowerBITranslator.

        Returns:
            Definitions: A Definitions object which will build and return the Power BI content.
        """
        return Definitions(
            assets=self.build_assets(
                dagster_powerbi_translator=dagster_powerbi_translator,
                enable_refresh_semantic_models=enable_refresh_semantic_models,
            )
        )


class PowerBICacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        workspace: PowerBIWorkspace,
        translator: Type[DagsterPowerBITranslator],
        enable_refresh_semantic_models: bool,
    ):
        self._workspace = workspace
        self._translator_cls = translator
        self._enable_refresh_semantic_models = enable_refresh_semantic_models
        super().__init__(unique_id=self._workspace.workspace_id)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        resolved_workspace = self._workspace.process_config_and_initialize()
        workspace_data: PowerBIWorkspaceData = resolved_workspace.fetch_powerbi_workspace_data()
        return [
            AssetsDefinitionCacheableData(extra_metadata=data.to_cached_data())
            for data in [
                *workspace_data.dashboards_by_id.values(),
                *workspace_data.reports_by_id.values(),
                *workspace_data.semantic_models_by_id.values(),
                *workspace_data.data_sources_by_id.values(),
            ]
        ]

    def build_definitions(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
    ) -> Sequence[AssetsDefinition]:
        workspace_data = PowerBIWorkspaceData.from_content_data(
            self._workspace.workspace_id,
            [
                PowerBIContentData.from_cached_data(check.not_none(entry.extra_metadata))
                for entry in data
            ],
        )

        translator = self._translator_cls(context=workspace_data)

        if self._enable_refresh_semantic_models:
            all_external_data = [
                *workspace_data.dashboards_by_id.values(),
                *workspace_data.reports_by_id.values(),
            ]
            all_executable_data = [*workspace_data.semantic_models_by_id.values()]
        else:
            all_external_data = [
                *workspace_data.dashboards_by_id.values(),
                *workspace_data.reports_by_id.values(),
                *workspace_data.semantic_models_by_id.values(),
            ]
            all_executable_data = []

        all_external_asset_specs = [
            translator.get_asset_spec(content) for content in all_external_data
        ]
        all_executable_asset_specs = [
            translator.get_asset_spec(content) for content in all_executable_data
        ]

        executable_assets = []
        for content, spec in zip(all_executable_data, all_executable_asset_specs):
            dataset_id = content.properties["id"]

            resource_key = f"power_bi_{self._workspace.workspace_id.replace('-','_')}"

            @multi_asset(
                specs=[spec],
                name="_".join(spec.key.path),
                resource_defs={resource_key: self._workspace.get_resource_definition()},
            )
            def asset_fn(context: AssetExecutionContext) -> None:
                power_bi = cast(PowerBIWorkspace, getattr(context.resources, resource_key))
                power_bi.trigger_refresh(dataset_id)
                power_bi.poll_refresh(dataset_id)
                context.log.info("Refresh completed.")

            executable_assets.append(asset_fn)

        return [*external_assets_from_specs(all_external_asset_specs), *executable_assets]
