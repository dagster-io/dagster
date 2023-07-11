from typing import TYPE_CHECKING, Any, List, Mapping, Optional

from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    OpExecutionContext,
    ScheduleDefinition,
    _check as check,
    define_asset_job,
    get_dagster_logger,
)
from dagster._core.errors import DagsterInvalidInvocationError

from .asset_utils import output_name_fn
from .dagster_dbt_translator import DagsterDbtTranslator
from .dbt_manifest_asset_selection import DbtManifestAssetSelection
from .utils import get_node_info_by_dbt_unique_id_from_manifest

logger = get_dagster_logger()


if TYPE_CHECKING:
    from dagster import RunConfig


class DbtAssetsDefinition(AssetsDefinition):
    def __init__(
        self,
        *,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        **kwargs: Any,
    ):
        check.dict_param(manifest, "manifest", key_type=str)
        check.inst_param(dagster_dbt_translator, "dagster_dbt_translator", DagsterDbtTranslator)

        super().__init__(**kwargs)
        self._manifest = manifest
        self._dagster_dbt_translator = dagster_dbt_translator
        self._node_info_by_dbt_unique_id = get_node_info_by_dbt_unique_id_from_manifest(manifest)

    @staticmethod
    def from_assets_def(
        assets_def: AssetsDefinition,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
    ) -> "DbtAssetsDefinition":
        check.dict_param(manifest, "manifest", key_type=str)
        check.inst_param(dagster_dbt_translator, "dagster_dbt_translator", DagsterDbtTranslator)

        return DbtAssetsDefinition(
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
            **assets_def.get_attributes_dict(),
        )

    def get_attributes_dict(self) -> Mapping[str, Any]:
        return dict(
            **super().get_attributes_dict(),
            manifest=self.manifest,
            dagster_dbt_translator=self.dagster_dbt_translator,
        )

    @property
    def dagster_dbt_translator(self) -> DagsterDbtTranslator:
        return self._dagster_dbt_translator

    @property
    def manifest(self) -> Mapping[str, Any]:
        return self._manifest

    @property
    def node_info_by_asset_key(self) -> Mapping[AssetKey, Mapping[str, Any]]:
        """A mapping of the default asset key for a dbt node to the node's dictionary representation in the manifest.
        """
        return {
            self.dagster_dbt_translator.node_info_to_asset_key(node): node
            for node in self._node_info_by_dbt_unique_id.values()
        }

    @property
    def node_info_by_output_name(self) -> Mapping[str, Mapping[str, Any]]:
        """A mapping of the default output name for a dbt node to the node's dictionary representation in the manifest.
        """
        return {output_name_fn(node): node for node in self._node_info_by_dbt_unique_id.values()}

    @property
    def descriptions_by_asset_key(self) -> Mapping[AssetKey, str]:
        """A mapping of the default asset key for a dbt node to the node's description in the manifest.
        """
        return {
            self.dagster_dbt_translator.node_info_to_asset_key(
                node
            ): self.dagster_dbt_translator.node_info_to_description(node)
            for node in self._node_info_by_dbt_unique_id.values()
        }

    @property
    def metadata_by_asset_key(self) -> Mapping[AssetKey, Mapping[Any, str]]:
        """A mapping of the default asset key for a dbt node to the node's metadata in the manifest.
        """
        return {
            self.dagster_dbt_translator.node_info_to_asset_key(
                node
            ): self.dagster_dbt_translator.node_info_to_metadata(node)
            for node in self._node_info_by_dbt_unique_id.values()
        }

    def get_node_info_for_output_name(self, output_name: str) -> Mapping[str, Any]:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.node_info_by_output_name[output_name]

    def get_asset_key_for_output_name(self, output_name: str) -> AssetKey:
        """Return the corresponding dbt node's Dagster asset key for a Dagster output name.

        Args:
            output_name (str): The Dagster output name.

        Returns:
            AssetKey: The corresponding dbt node's Dagster asset key.
        """
        return self.dagster_dbt_translator.node_info_to_asset_key(
            self.get_node_info_for_output_name(output_name)
        )

    def get_asset_key_for_dbt_unique_id(self, unique_id: str) -> AssetKey:
        node_info = self._node_info_by_dbt_unique_id.get(unique_id)

        if not node_info:
            raise DagsterInvalidInvocationError(
                f"Could not find a dbt node with unique_id: {unique_id}. A unique ID consists of"
                " the node type (model, source, seed, etc.), project name, and node name in a"
                " dot-separated string. For example: model.my_project.my_model\n For more"
                " information on the unique ID structure:"
                " https://docs.getdbt.com/reference/artifacts/manifest-json"
            )

        return self.dagster_dbt_translator.node_info_to_asset_key(node_info)

    def get_asset_key_for_source(self, source_name: str) -> AssetKey:
        """Returns the corresponding Dagster asset key for a dbt source with a singular table.

        Args:
            source_name (str): The name of the dbt source.

        Raises:
            DagsterInvalidInvocationError: If the source has more than one table.

        Returns:
            AssetKey: The corresponding Dagster asset key.

        Examples:
            .. code-block:: python

                from dagster import asset
                from dagster_dbt import dbt_assets

                @dbt_assets(manifest=...)
                def all_dbt_assets():
                    ...

                @asset(key=all_dbt_assets.get_asset_key_for_source("my_source"))
                def upstream_python_asset():
                    ...
        """
        asset_keys_by_output_name = self.get_asset_keys_by_output_name_for_source(source_name)

        if len(asset_keys_by_output_name) > 1:
            raise DagsterInvalidInvocationError(
                f"Source {source_name} has more than one table:"
                f" {asset_keys_by_output_name.values()}. Use"
                " `get_asset_keys_by_output_name_for_source` instead to get all tables for a"
                " source."
            )

        return list(asset_keys_by_output_name.values())[0]

    def get_asset_keys_by_output_name_for_source(self, source_name: str) -> Mapping[str, AssetKey]:
        """Returns the corresponding Dagster asset keys for all tables in a dbt source.

        This is a convenience method that makes it easy to define a multi-asset that generates
        all the tables for a given dbt source.

        Args:
            source_name (str): The name of the dbt source.

        Returns:
            Mapping[str, AssetKey]: A mapping of the table name to corresponding Dagster asset key
                for all tables in the given dbt source.

        Examples:
            .. code-block:: python

                from dagster import AssetOut, multi_asset
                from dagster_dbt import dbt_assets

                @dbt_assets(manifest=...)
                def all_dbt_assets():
                    ...

                @multi_asset(
                    outs={
                        name: AssetOut(key=asset_key)
                        for name, asset_key in all_dbt_assets.get_asset_keys_by_output_name_for_source(
                            "raw_data"
                        ).items()
                    },
                )
                def upstream_python_asset():
                    ...

        """
        check.str_param(source_name, "source_name")

        matching_nodes = [
            value
            for value in self._manifest["sources"].values()
            if value["source_name"] == source_name
        ]

        if len(matching_nodes) == 0:
            raise DagsterInvalidInvocationError(
                f"Could not find a dbt source with name: {source_name}"
            )

        return {
            output_name_fn(value): self.dagster_dbt_translator.node_info_to_asset_key(value)
            for value in matching_nodes
        }

    def get_asset_key_for_model(self, model_name: str) -> AssetKey:
        """Return the corresponding Dagster asset key for a dbt model.

        Args:
            model_name (str): The name of the dbt model.

        Returns:
            AssetKey: The corresponding Dagster asset key.

        Examples:
            .. code-block:: python

                from dagster import asset
                from dagster_dbt import dbt_assets

                @dbt_assets(manifest=...)
                def all_dbt_assets():
                    ...


                @asset(non_argument_deps={all_dbt_assets.get_asset_key_for_model("customers")})
                def cleaned_customers():
                    ...
        """
        check.str_param(model_name, "model_name")

        matching_models = [
            value
            for value in self._manifest["nodes"].values()
            if value["name"] == model_name and value["resource_type"] == "model"
        ]

        if len(matching_models) == 0:
            raise DagsterInvalidInvocationError(
                f"Could not find a dbt model with name: {model_name}"
            )

        return self.dagster_dbt_translator.node_info_to_asset_key(next(iter(matching_models)))

    def build_dbt_asset_selection(
        self,
        dbt_select: str = "fqn:*",
        dbt_exclude: Optional[str] = None,
    ) -> AssetSelection:
        """Build an asset selection for a dbt selection string.

        See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work for
        more information.

        Args:
            dbt_select (str): A dbt selection string to specify a set of dbt resources.
            dbt_exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.

        Returns:
            AssetSelection: An asset selection for the selected dbt nodes.

        Examples:
            .. code-block:: python

                from dagster_dbt import dbt_assets

                @dbt_assets(manifest=...)
                def all_dbt_assets():
                    ...

                # Select the dbt assets that have the tag "foo".
                my_selection = all_dbt_assets.build_dbt_asset_selection(dbt_select="tag:foo")
        """
        return DbtManifestAssetSelection(
            manifest=self._manifest,
            select=dbt_select,
            exclude=dbt_exclude,
        )

    def build_schedule_from_dbt_select(
        self,
        job_name: str,
        cron_schedule: str,
        dbt_select: str = "fqn:*",
        dbt_exclude: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        config: Optional["RunConfig"] = None,
        execution_timezone: Optional[str] = None,
    ) -> ScheduleDefinition:
        """Build a schedule to materialize a specified set of dbt resources from a dbt selection string.

        See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work for
        more information.

        Args:
            job_name (str): The name of the job to materialize the dbt resources.
            cron_schedule (str): The cron schedule to define the schedule.
            dbt_select (str): A dbt selection string to specify a set of dbt resources.
            dbt_exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.
            tags (Optional[Mapping[str, str]]): A dictionary of tags (string key-value pairs) to attach
                to the scheduled runs.
            config (Optional[RunConfig]): The config that parameterizes the execution of this schedule.
            execution_timezone (Optional[str]): Timezone in which the schedule should run.
                Supported strings for timezones are the ones provided by the
                `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".

        Returns:
            ScheduleDefinition: A definition to materialize the selected dbt resources on a cron schedule.

        Examples:
            .. code-block:: python

                from dagster_dbt import dbt_assets

                @dbt_assets(manifest=...)
                def all_dbt_assets():
                    ...

                daily_dbt_assets_schedule = all_dbt_assets.build_schedule_from_dbt_select(
                    job_name="all_dbt_assets",
                    cron_schedule="0 0 * * *",
                    dbt_select="fqn:*",
                )
        """
        return ScheduleDefinition(
            cron_schedule=cron_schedule,
            job=define_asset_job(
                name=job_name,
                selection=self.build_dbt_asset_selection(
                    dbt_select=dbt_select,
                    dbt_exclude=dbt_exclude,
                ),
                config=config,
                tags=tags,
            ),
            execution_timezone=execution_timezone,
        )

    def get_subset_selection_for_context(
        self,
        context: OpExecutionContext,
        select: Optional[str] = None,
        exclude: Optional[str] = None,
    ) -> List[str]:
        """Generate a dbt selection string to materialize the selected resources in a subsetted execution context.

        See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work.

        Args:
            context (OpExecutionContext): The execution context for the current execution step.
            select (Optional[str]): A dbt selection string to select resources to materialize.
            exclude (Optional[str]): A dbt selection string to exclude resources from materializing.

        Returns:
            List[str]: dbt CLI arguments to materialize the selected resources in a
                subsetted execution context.

                If the current execution context is not performing a subsetted execution,
                return CLI arguments composed of the inputed selection and exclusion arguments.
        """
        default_dbt_selection = []
        if select:
            default_dbt_selection += ["--select", select]
        if exclude:
            default_dbt_selection += ["--exclude", exclude]

        # TODO: this should be a property on the context if this is a permanent indicator for
        # determining whether the current execution context is performing a subsetted execution.
        is_subsetted_execution = len(context.selected_output_names) != len(
            context.assets_def.node_keys_by_output_name
        )
        if not is_subsetted_execution:
            logger.info(
                "A dbt subsetted execution is not being performed. Using the default dbt selection"
                f" arguments `{default_dbt_selection}`."
            )
            return default_dbt_selection

        selected_dbt_resources = []
        for output_name in context.selected_output_names:
            node_info = self.get_node_info_for_output_name(output_name)

            # Explicitly select a dbt resource by its fully qualified name (FQN).
            # https://docs.getdbt.com/reference/node-selection/methods#the-file-or-fqn-method
            fqn_selector = f"fqn:{'.'.join(node_info['fqn'])}"

            selected_dbt_resources.append(fqn_selector)

        # Take the union of all the selected resources.
        # https://docs.getdbt.com/reference/node-selection/set-operators#unions
        union_selected_dbt_resources = ["--select"] + [" ".join(selected_dbt_resources)]

        logger.info(
            "A dbt subsetted execution is being performed. Overriding default dbt selection"
            f" arguments `{default_dbt_selection}` with arguments: `{union_selected_dbt_resources}`"
        )

        return union_selected_dbt_resources
