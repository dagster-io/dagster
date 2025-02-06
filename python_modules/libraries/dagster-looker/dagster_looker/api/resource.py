from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from dagster import (
    AssetSpec,
    ConfigurableResource,
    Definitions,
    _check as check,
)
from dagster._annotations import beta, deprecated, public
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._utils.log import get_dagster_logger
from dagster._utils.warnings import deprecation_warning
from looker_sdk import init40
from looker_sdk.rtl.api_settings import ApiSettings, SettingsConfig
from looker_sdk.sdk.api40.methods import Looker40SDK
from pydantic import Field

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    LookerInstanceData,
    LookerStructureData,
    LookerStructureType,
    RequestStartPdtBuild,
)

if TYPE_CHECKING:
    from looker_sdk.sdk.api40.models import Folder, LookmlModelExplore


logger = get_dagster_logger("dagster_looker")


LOOKER_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-looker/reconstruction_metadata"


@record
class LookerFilter:
    """Filters the set of Looker objects to fetch.

    Args:
        dashboard_folders (Optional[List[List[str]]]): A list of folder paths to fetch dashboards from.
            Each folder path is a list of folder names, starting from the root folder. All dashboards
            contained in the specified folders will be fetched. If not provided, all dashboards will be fetched.
        only_fetch_explores_used_in_dashboards (bool): If True, only explores used in the fetched dashboards
            will be fetched. If False, all explores will be fetched. Defaults to False.
    """

    dashboard_folders: Optional[list[list[str]]] = None
    only_fetch_explores_used_in_dashboards: bool = False


@beta
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
    @deprecated(
        breaking_version="1.9.0",
        additional_warn_text="Use dagster_looker.load_looker_asset_specs instead",
    )
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
        from dagster_looker.api.assets import build_looker_pdt_assets_definitions

        resource_key = "looker"
        translator = dagster_looker_translator or DagsterLookerApiTranslator()

        pdts = build_looker_pdt_assets_definitions(
            resource_key=resource_key,
            request_start_pdt_builds=request_start_pdt_builds or [],
            dagster_looker_translator=translator,
        )

        return Definitions(
            assets=[*pdts, *load_looker_asset_specs(self, translator, looker_filter)],
            resources={resource_key: self},
        )


@beta
def load_looker_asset_specs(
    looker_resource: LookerResource,
    dagster_looker_translator: Optional[
        Union[DagsterLookerApiTranslator, type[DagsterLookerApiTranslator]]
    ] = None,
    looker_filter: Optional[LookerFilter] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Looker structures.

    Args:
        looker_resource (LookerResource): The Looker resource to fetch assets from.
        dagster_looker_translator (Optional[Union[DagsterLookerApiTranslator, Type[DagsterLookerApiTranslator]]]):
            The translator to use to convert Looker structures into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterLookerApiTranslator`.

    Returns:
        List[AssetSpec]: The set of AssetSpecs representing the Looker structures.
    """
    if isinstance(dagster_looker_translator, type):
        deprecation_warning(
            subject="Support of `dagster_looker_translator` as a Type[DagsterLookerApiTranslator]",
            breaking_version="1.10",
            additional_warn_text=(
                "Pass an instance of DagsterLookerApiTranslator or subclass to `dagster_looker_translator` instead."
            ),
        )
        dagster_looker_translator = dagster_looker_translator()

    return check.is_list(
        LookerApiDefsLoader(
            looker_resource=looker_resource,
            translator=dagster_looker_translator or DagsterLookerApiTranslator(),
            looker_filter=looker_filter or LookerFilter(),
        )
        .build_defs()
        .assets,
        AssetSpec,
    )


def build_folder_path(folder_id_to_folder: dict[str, "Folder"], folder_id: str) -> list[str]:
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
    looker_filter: LookerFilter

    @property
    def defs_key(self) -> str:
        return f"{LOOKER_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.looker_resource.client_id}"

    def fetch_state(self) -> Mapping[str, Any]:
        looker_instance_data = self.fetch_looker_instance_data()
        return looker_instance_data.to_state(self.looker_resource.get_sdk())

    def defs_from_state(self, state: Mapping[str, Any]) -> Definitions:
        looker_instance_data = LookerInstanceData.from_state(self.looker_resource.get_sdk(), state)
        return self._build_defs_from_looker_instance_data(looker_instance_data, self.translator)

    def _build_defs_from_looker_instance_data(
        self,
        looker_instance_data: LookerInstanceData,
        dagster_looker_translator: DagsterLookerApiTranslator,
    ) -> Definitions:
        explores = [
            dagster_looker_translator.get_asset_spec(
                LookerApiTranslatorStructureData(
                    structure_data=LookerStructureData(
                        structure_type=LookerStructureType.EXPLORE,
                        data=lookml_explore,
                        base_url=self.looker_resource.base_url,
                    ),
                    instance_data=looker_instance_data,
                )
            )
            for lookml_explore in looker_instance_data.explores_by_id.values()
        ]
        views = [
            dagster_looker_translator.get_asset_spec(
                LookerApiTranslatorStructureData(
                    structure_data=LookerStructureData(
                        structure_type=LookerStructureType.DASHBOARD,
                        data=looker_dashboard,
                        base_url=self.looker_resource.base_url,
                    ),
                    instance_data=looker_instance_data,
                )
            )
            for looker_dashboard in looker_instance_data.dashboards_by_id.values()
        ]
        return Definitions(assets=[*explores, *views])

    def fetch_looker_instance_data(self) -> LookerInstanceData:
        """Fetches all explores and dashboards from the Looker instance.

        TODO: Fetch explores in parallel using asyncio
        TODO: Get all the LookML views upstream of the explores
        """
        sdk = self.looker_resource.get_sdk()

        folders = sdk.all_folders()
        folder_by_id = {folder.id: folder for folder in folders if folder.id is not None}

        # Get dashboards
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

        dashboard_ids_to_fetch = []
        if len(folder_filter_strings) == 0:
            dashboard_ids_to_fetch = [
                dashboard.id for dashboard in dashboards if not dashboard.hidden
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
                    if any(
                        folder_string.startswith(folder_filter_string)
                        for folder_filter_string in folder_filter_strings
                    ):
                        dashboard_ids_to_fetch.append(dashboard.id)

        with ThreadPoolExecutor(max_workers=None) as executor:
            dashboards_by_id = dict(
                list(
                    executor.map(
                        lambda dashboard_id: (
                            dashboard_id,
                            sdk.dashboard(dashboard_id=dashboard_id),
                        ),
                        (dashboard_id for dashboard_id in dashboard_ids_to_fetch),
                    )
                )
            )

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
                for dash_filter in dashboard.dashboard_filters or []:
                    used_explores.add((dash_filter.model, dash_filter.explore))

            explores_for_model = {
                model_name: [
                    explore_name
                    for explore_name in explore_names
                    if (model_name, explore_name) in used_explores
                ]
                for model_name, explore_names in explores_for_model.items()
            }

        def fetch_explore(model_name, explore_name) -> Optional[tuple[str, "LookmlModelExplore"]]:
            try:
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
                    list[tuple[str, "LookmlModelExplore"]],
                    (
                        entry
                        for entry in executor.map(
                            lambda explore: fetch_explore(*explore), explores_to_fetch
                        )
                        if entry is not None
                    ),
                )
            )

        user_ids_to_fetch = set()
        for dashboard in dashboards_by_id.values():
            if dashboard.user_id:
                user_ids_to_fetch.update(dashboard.user_id)
        users = sdk.search_users(id=",".join(user_ids_to_fetch))

        return LookerInstanceData(
            explores_by_id=explores_by_id,
            dashboards_by_id=dashboards_by_id,
            users_by_id={check.not_none(user.id): user for user in users},
        )
