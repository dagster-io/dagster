from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Tuple, cast

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    ConfigurableResource,
    Definitions,
    Failure,
    _check as check,
    multi_asset,
)
from dagster._annotations import experimental, public
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._utils.log import get_dagster_logger
from looker_sdk import init40
from looker_sdk.rtl.api_settings import ApiSettings, SettingsConfig
from looker_sdk.sdk.api40.methods import Looker40SDK
from pydantic import Field

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerInstanceData,
    LookerStructureData,
    LookerStructureType,
    LookmlView,
    RequestStartPdtBuild,
)

if TYPE_CHECKING:
    from looker_sdk.sdk.api40.models import Folder, LookmlModelExplore


logger = get_dagster_logger("dagster_looker")


LOOKER_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-looker/reconstruction_metadata"


@record
class LookerFilter:
    dashboard_folders: Optional[List[List[str]]] = None
    excluded_dashboard_folders: Optional[List[List[str]]] = None
    only_fetch_explores_used_in_dashboards: bool = False


@experimental
class LookerResource(ConfigurableResource):
    """Represents a connection to a Looker instance and provides methods
    to interact with the Looker API.
    """

    base_url: str = Field(
        ...,
        description="Base URL for the Looker API. For example, https://your.cloud.looker.com.",
    )
    client_id: str = Field(..., description="Client ID for the Looker API.")
    client_secret: str = Field(..., description="Client secret for the Looker API.")

    @cached_method
    def get_sdk(self) -> Looker40SDK:
        class DagsterLookerApiSettings(ApiSettings):
            def read_config(_self) -> SettingsConfig:
                return {
                    **super().read_config(),
                    "base_url": self.base_url,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }

        return init40(config_settings=DagsterLookerApiSettings())

    @public
    def build_defs(
        self,
        *,
        request_start_pdt_builds: Optional[Sequence[RequestStartPdtBuild]] = None,
        dagster_looker_translator: Optional[DagsterLookerApiTranslator] = None,
        looker_filter: Optional[LookerFilter] = None,
    ) -> Definitions:
        """Returns a Definitions object which will load structures from the Looker instance
        and translate it into assets, using the provided translator.

        Args:
            request_start_pdt_builds (Optional[Sequence[RequestStartPdtBuild]]): A list of
                requests to start PDT builds. See https://developers.looker.com/api/explorer/4.0/types/DerivedTable/RequestStartPdtBuild?sdk=py
                for documentation on all available fields.
            dagster_looker_translator (Optional[DagsterLookerApiTranslator]): The translator to
                use to convert Looker structures into assets. Defaults to DagsterLookerApiTranslator.

        Returns:
            Definitions: A Definitions object which will contain return the Looker structures as assets.
        """
        return LookerApiDefsLoader(
            looker_resource=self,
            translator=dagster_looker_translator
            if dagster_looker_translator is not None
            else DagsterLookerApiTranslator(),
            request_start_pdt_builds=request_start_pdt_builds or [],
            looker_filter=looker_filter or LookerFilter(),
        ).build_defs()


def build_folder_path(folder_id_to_folder: Dict[str, "Folder"], folder_id: str) -> List[str]:
    curr = folder_id
    result = []
    while curr in folder_id_to_folder:
        result = [folder_id_to_folder[curr].name] + result
        curr = folder_id_to_folder[curr].parent_id
    return result


@dataclass(frozen=True)
class LookerApiDefsLoader(StateBackedDefinitionsLoader[Mapping[str, Any]]):
    looker_resource: LookerResource
    translator: DagsterLookerApiTranslator
    request_start_pdt_builds: Sequence[RequestStartPdtBuild]
    looker_filter: LookerFilter

    @property
    def defs_key(self) -> str:
        return f"{LOOKER_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.looker_resource.client_id}"

    def fetch_state(self) -> Mapping[str, Any]:
        looker_instance_data = self.fetch_looker_instance_data()
        return looker_instance_data.to_state(self.looker_resource.get_sdk())

    def defs_from_state(self, state: Mapping[str, Any]) -> Definitions:
        looker_instance_data = LookerInstanceData.from_state(self.looker_resource.get_sdk(), state)
        return self._build_defs_from_looker_instance_data(
            looker_instance_data, self.request_start_pdt_builds or [], self.translator
        )

    def _build_defs_from_looker_instance_data(
        self,
        looker_instance_data: LookerInstanceData,
        request_start_pdt_builds: Sequence[RequestStartPdtBuild],
        dagster_looker_translator: DagsterLookerApiTranslator,
    ) -> Definitions:
        pdts = self._build_pdt_defs(request_start_pdt_builds, dagster_looker_translator)
        explores = [
            dagster_looker_translator.get_asset_spec(
                LookerStructureData(structure_type=LookerStructureType.EXPLORE, data=lookml_explore)
            )
            for lookml_explore in looker_instance_data.explores_by_id.values()
        ]
        views = [
            dagster_looker_translator.get_asset_spec(
                LookerStructureData(
                    structure_type=LookerStructureType.DASHBOARD, data=looker_dashboard
                )
            )
            for looker_dashboard in looker_instance_data.dashboards_by_id.values()
        ]

        return Definitions(assets=[*pdts, *explores, *views])

    def _build_pdt_defs(
        self,
        request_start_pdt_builds: Sequence[RequestStartPdtBuild],
        dagster_looker_translator: DagsterLookerApiTranslator,
    ) -> Sequence[AssetsDefinition]:
        result = []
        for request_start_pdt_build in request_start_pdt_builds:

            @multi_asset(
                specs=[
                    dagster_looker_translator.get_asset_spec(
                        LookerStructureData(
                            structure_type=LookerStructureType.VIEW,
                            data=LookmlView(
                                view_name=request_start_pdt_build.view_name,
                                sql_table_name=None,
                            ),
                        )
                    )
                ],
                name=f"{request_start_pdt_build.model_name}_{request_start_pdt_build.view_name}",
                resource_defs={"looker": self.looker_resource},
            )
            def pdts(context: AssetExecutionContext):
                looker: "LookerResource" = context.resources.looker

                context.log.info(
                    f"Starting pdt build for Looker view `{request_start_pdt_build.view_name}` in Looker model `{request_start_pdt_build.model_name}`."
                )

                materialize_pdt = looker.get_sdk().start_pdt_build(
                    model_name=request_start_pdt_build.model_name,
                    view_name=request_start_pdt_build.view_name,
                    force_rebuild=request_start_pdt_build.force_rebuild,
                    force_full_incremental=request_start_pdt_build.force_full_incremental,
                    workspace=request_start_pdt_build.workspace,
                    source=f"Dagster run {context.run_id}" or request_start_pdt_build.source,
                )

                if not materialize_pdt.materialization_id:
                    raise Failure("No materialization id was returned from Looker API.")

                check_pdt = looker.get_sdk().check_pdt_build(
                    materialization_id=materialize_pdt.materialization_id
                )

                context.log.info(
                    f"Materialization id: {check_pdt.materialization_id}, "
                    f"response text: {check_pdt.resp_text}"
                )

            result.append(pdts)

        return result

    def fetch_looker_instance_data(self) -> LookerInstanceData:
        """Fetches all explores and dashboards from the Looker instance.

        TODO: Fetch explores in parallel using asyncio
        TODO: Get all the LookML views upstream of the explores
        """
        sdk = self.looker_resource.get_sdk()

        logger.debug("Fetching Looker instance data")
        folders = sdk.all_folders()
        folder_by_id = {folder.id: folder for folder in folders if folder.id is not None}

        # Get dashboards
        logger.debug("Fetching dashboard list")
        dashboards = sdk.all_dashboards(
            fields=",".join(
                [
                    "id",
                    "hidden",
                    "folder",
                ]
            )
        )

        folder_filter_strings = (
            [
                "/".join(folder_filter).lower()
                for folder_filter in self.looker_filter.dashboard_folders
            ]
            if self.looker_filter.dashboard_folders
            else []
        )
        excluded_folder_filter_strings = (
            [
                "/".join(folder_filter).lower()
                for folder_filter in self.looker_filter.excluded_dashboard_folders
            ]
            if self.looker_filter.excluded_dashboard_folders
            else []
        )

        check.invariant(
            len(folder_filter_strings) == 0 or len(excluded_folder_filter_strings) == 0,
            "Cannot specify both included and excluded folder filters",
        )

        logger.debug(f"Fetching dashboard details with folder filters: {folder_filter_strings}")
        dashboard_ids_to_fetch: List[str] = []
        if len(folder_filter_strings) == 0 and len(excluded_folder_filter_strings) == 0:
            dashboard_ids_to_fetch = [
                check.not_none(dashboard.id) for dashboard in dashboards if not dashboard.hidden
            ]
        else:
            for dashboard in dashboards:
                if (
                    not dashboard.hidden
                    and dashboard.folder is not None
                    and dashboard.folder.id is not None
                ):
                    folder_string = "/".join(
                        build_folder_path(folder_by_id, dashboard.folder.id)
                    ).lower()
                    if len(folder_filter_strings) > 0:
                        if any(
                            folder_string.startswith(folder_filter_string)
                            for folder_filter_string in folder_filter_strings
                        ):
                            dashboard_ids_to_fetch.append(check.not_none(dashboard.id))
                    else:
                        if not any(
                            folder_string.startswith(folder_filter_string)
                            for folder_filter_string in excluded_folder_filter_strings
                        ):
                            dashboard_ids_to_fetch.append(check.not_none(dashboard.id))

        dashboards_by_id = {
            check.not_none(dashboard.id): dashboard
            for dashboard in sdk.search_dashboards(
                id=",".join(dashboard_ids_to_fetch),
            )
        }

        logger.debug("Fetching models and associated explore ids")
        # Get explore names from models
        explores_for_model = {
            model.name: [explore.name for explore in (model.explores or []) if explore.name]
            for model in sdk.all_lookml_models(
                fields=",".join(
                    [
                        "name",
                        "explores",
                    ]
                )
            )
            if model.name
        }

        if self.looker_filter.only_fetch_explores_used_in_dashboards:
            used_explores = set()
            for dashboard in dashboards_by_id.values():
                for filter in dashboard.dashboard_filters or []:
                    used_explores.add((filter.model, filter.explore))

            explores_for_model = {
                model_name: [
                    explore_name
                    for explore_name in explore_names
                    if (model_name, explore_name) in used_explores
                ]
                for model_name, explore_names in explores_for_model.items()
            }

        def fetch_explore(model_name, explore_name) -> Optional[Tuple[str, "LookmlModelExplore"]]:
            try:
                logger.debug(f"Fetching LookML explore '{explore_name}' for model '{model_name}'")
                lookml_explore = sdk.lookml_model_explore(
                    lookml_model_name=model_name,
                    explore_name=explore_name,
                    fields=",".join(
                        [
                            "id",
                            "view_name",
                            "sql_table_name",
                            "joins",
                        ]
                    ),
                )

                return (check.not_none(lookml_explore.id), lookml_explore)
            except:
                logger.warning(
                    f"Failed to fetch LookML explore '{explore_name}' for model '{model_name}'."
                )

        with ThreadPoolExecutor(max_workers=None) as executor:
            explores_to_fetch = [
                (model_name, explore_name)
                for model_name, explore_names in explores_for_model.items()
                for explore_name in explore_names
            ]

            explores_by_id = dict(
                cast(
                    List[Tuple[str, "LookmlModelExplore"]],
                    (
                        entry
                        for entry in executor.map(
                            lambda explore: fetch_explore(*explore), explores_to_fetch
                        )
                        if entry is not None
                    ),
                )
            )

        return LookerInstanceData(
            explores_by_id=explores_by_id,
            dashboards_by_id=dashboards_by_id,
        )
