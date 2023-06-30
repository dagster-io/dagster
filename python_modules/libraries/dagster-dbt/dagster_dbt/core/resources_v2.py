import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

import dateutil.parser
from dagster import (
    AssetKey,
    AssetObservation,
    AssetSelection,
    ConfigurableResource,
    OpExecutionContext,
    Output,
    ScheduleDefinition,
    _check as check,
    define_asset_job,
    get_dagster_logger,
)
from dagster._annotations import experimental
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.errors import DagsterInvalidInvocationError
from dbt.contracts.results import NodeStatus
from dbt.node_types import NodeType
from pydantic import Field
from typing_extensions import Literal

from ..asset_utils import (
    default_asset_key_fn,
    default_description_fn,
    default_metadata_fn,
    is_non_asset_node,
    output_name_fn,
)
from ..errors import DagsterDbtCliRuntimeError
from ..utils import ASSET_RESOURCE_TYPES, select_unique_ids_from_manifest

if TYPE_CHECKING:
    from dagster import RunConfig

logger = get_dagster_logger()


PARTIAL_PARSE_FILE_NAME = "partial_parse.msgpack"


@experimental
@dataclass
class DbtManifest:
    """A wrapper class around the dbt manifest to translate dbt concepts to Dagster concepts.

    Args:
        raw_manifest (Dict[str, Any]): The raw dictionary representation of the dbt manifest.

    Examples:
        .. code-block:: python

            from dagster_dbt import DbtManifest

            manifest = DbtManifest.read(path="path/to/manifest.json")
    """

    raw_manifest: Mapping[str, Any]

    @classmethod
    def read(cls, path: Union[str, os.PathLike]) -> "DbtManifest":
        """Read the file path to a dbt manifest and create a DbtManifest object.

        Args:
            path(Union[str, os.PathLike]): The path to the dbt manifest.json file.

        Returns:
            DbtManifest: A DbtManifest object.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtManifest

                manifest = DbtManifest.read(path="path/to/manifest.json")
        """
        with open(path, "r") as handle:
            raw_manifest: Dict[str, Any] = json.loads(handle.read())

        return cls(raw_manifest=raw_manifest)

    @property
    def node_info_by_dbt_unique_id(self) -> Mapping[str, Mapping[str, Any]]:
        """A mapping of a dbt node's unique id to the node's dictionary representation in the manifest.
        """
        return {
            **self.raw_manifest["nodes"],
            **self.raw_manifest["sources"],
            **self.raw_manifest["exposures"],
            **self.raw_manifest["metrics"],
        }

    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        """A function that takes a dictionary representing the dbt node and returns the
        Dagster asset key the represents the dbt node.

        This method can be overridden to provide a custom asset key for a dbt node.

        Args:
            node_info (Mapping[str, Any]): A dictionary representing the dbt node.

        Returns:
            AssetKey: The Dagster asset key for the dbt node.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster import AssetKey
                from dagster_dbt import DbtManifest


                class CustomizedDbtManifest(DbtManifest):
                    @classmethod
                    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
                        return AssetKey(["prefix", node_info["alias"]])


                manifest = CustomizedDbtManifest.read(path="path/to/manifest.json")
        """
        return default_asset_key_fn(node_info)

    @classmethod
    def node_info_to_description(cls, node_info: Mapping[str, Any]) -> str:
        """A function that takes a dictionary representing the dbt node and returns the
        Dagster description the represents the dbt node.

        This method can be overridden to provide a custom description for a dbt node.

        Args:
            node_info (Mapping[str, Any]): A dictionary representing the dbt node.

        Returns:
            str: The description for the dbt node.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DbtManifest


                class CustomizedDbtManifest(DbtManifest):
                    @classmethod
                    def node_info_to_description(cls, node_info: Mapping[str, Any]) -> str:
                        return "custom description"


                manifest = CustomizedDbtManifest.read(path="path/to/manifest.json")
        """
        return default_description_fn(node_info)

    @classmethod
    def node_info_to_metadata(cls, node_info: Mapping[str, Any]) -> Mapping[str, Any]:
        """A function that takes a dictionary representing the dbt node and returns the
        Dagster metadata the represents the dbt node.

        This method can be overridden to provide custom metadata for a dbt node.

        Args:
            node_info (Mapping[str, Any]): A dictionary representing the dbt node.

        Returns:
            Mapping[str, Any]: A dictionary representing the Dagster metadata for the dbt node.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DbtManifest


                class CustomizedDbtManifest(DbtManifest):
                    @classmethod
                    def node_info_to_metadata(cls, node_info: Mapping[str, Any]) -> Mapping[str, Any]:
                        return {"custom": "metadata"}


                manifest = CustomizedDbtManifest.read(path="path/to/manifest.json")
        """
        return default_metadata_fn(node_info)

    @property
    def node_info_by_asset_key(self) -> Mapping[AssetKey, Mapping[str, Any]]:
        """A mapping of the default asset key for a dbt node to the node's dictionary representation in the manifest.
        """
        return {
            self.node_info_to_asset_key(node): node
            for node in self.node_info_by_dbt_unique_id.values()
        }

    @property
    def node_info_by_output_name(self) -> Mapping[str, Mapping[str, Any]]:
        """A mapping of the default output name for a dbt node to the node's dictionary representation in the manifest.
        """
        return {output_name_fn(node): node for node in self.node_info_by_dbt_unique_id.values()}

    @property
    def asset_key_replacements(self) -> Mapping[AssetKey, AssetKey]:
        """A mapping of replacement asset keys for a dbt node to the node's dictionary representation in the manifest.
        """
        return {
            DbtManifest.node_info_to_asset_key(node_info): self.node_info_to_asset_key(node_info)
            for node_info in self.node_info_by_dbt_unique_id.values()
        }

    @property
    def descriptions_by_asset_key(self) -> Mapping[AssetKey, str]:
        """A mapping of the default asset key for a dbt node to the node's description in the manifest.
        """
        return {
            self.node_info_to_asset_key(node): self.node_info_to_description(node)
            for node in self.node_info_by_dbt_unique_id.values()
        }

    @property
    def metadata_by_asset_key(self) -> Mapping[AssetKey, Mapping[Any, str]]:
        """A mapping of the default asset key for a dbt node to the node's metadata in the manifest.
        """
        return {
            self.node_info_to_asset_key(node): self.node_info_to_metadata(node)
            for node in self.node_info_by_dbt_unique_id.values()
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
        return self.node_info_to_asset_key(self.get_node_info_for_output_name(output_name))

    def get_asset_key_for_dbt_unique_id(self, unique_id: str) -> AssetKey:
        node_info = self.node_info_by_dbt_unique_id.get(unique_id)

        if not node_info:
            raise DagsterInvalidInvocationError(
                f"Could not find a dbt node with unique_id: {unique_id}. A unique ID consists of"
                " the node type (model, source, seed, etc.), project name, and node name in a"
                " dot-separated string. For example: model.my_project.my_model\n For more"
                " information on the unique ID structure:"
                " https://docs.getdbt.com/reference/artifacts/manifest-json"
            )

        return self.node_info_to_asset_key(node_info)

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
                from dagster_dbt import DbtManifest

                manifest = DbtManifest.read("path/to/manifest.json")


                @asset(key=manifest.get_asset_key_for_source("my_source"))
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
                from dagster_dbt import DbtManifest

                manifest = DbtManifest.read("path/to/manifest.json")


                @multi_asset(
                    outs={
                        name: AssetOut(key=asset_key)
                        for name, asset_key in manifest.get_asset_keys_by_output_name_for_source(
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
            for value in self.raw_manifest["sources"].values()
            if value["source_name"] == source_name
        ]

        if len(matching_nodes) == 0:
            raise DagsterInvalidInvocationError(
                f"Could not find a dbt source with name: {source_name}"
            )

        return {
            output_name_fn(value): self.node_info_to_asset_key(value) for value in matching_nodes
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
                from dagster_dbt import DbtManifest

                manifest = DbtManifest.read("path/to/manifest.json")


                @asset(non_argument_deps={manifest.get_asset_key_for_model("customers")})
                def cleaned_customers():
                    ...
        """
        check.str_param(model_name, "model_name")

        matching_models = [
            value
            for value in self.raw_manifest["nodes"].values()
            if value["name"] == model_name and value["resource_type"] == "model"
        ]

        if len(matching_models) == 0:
            raise DagsterInvalidInvocationError(
                f"Could not find a dbt model with name: {model_name}"
            )

        return self.node_info_to_asset_key(next(iter(matching_models)))

    def build_asset_selection(
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

                from dagster_dbt import DbtManifest

                manifest = DbtManifest.read("path/to/manifest.json")

                # Select the dbt assets that have the tag "foo".
                my_selection = manifest.build_asset_selection(dbt_select="tag:foo")
        """
        return DbtManifestAssetSelection(
            manifest=self,
            select=dbt_select,
            exclude=dbt_exclude,
        )

    def build_schedule(
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

                from dagster_dbt import DbtManifest

                manifest = DbtManifest.read("path/to/manifest.json")

                daily_dbt_assets_schedule = manifest.build_schedule(
                    job_name="all_dbt_assets",
                    cron_schedule="0 0 * * *",
                    dbt_select="fqn:*",
                )
        """
        return ScheduleDefinition(
            cron_schedule=cron_schedule,
            job=define_asset_job(
                name=job_name,
                selection=self.build_asset_selection(
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


@experimental
class DbtManifestAssetSelection(AssetSelection):
    """Defines a selection of assets from a dbt manifest wrapper and a dbt selection string.

    Args:
        manifest (DbtManifest): The dbt manifest wrapper.
        select (str): A dbt selection string to specify a set of dbt resources.
        exclude (Optional[str]): A dbt selection string to exclude a set of dbt resources.

    Examples:
        .. code-block:: python

            from dagster_dbt import DbtManifest, DbtManifestAssetSelection

            manifest = DbtManifest.read("path/to/manifest.json")

            # Build the selection from the manifest: select the dbt assets that have the tag "foo".
            my_selection = manifest.build_asset_selection(dbt_select="tag:foo")

            # Or, manually build the same selection.
            my_selection = DbtManifestAssetSelection(manifest=manifest, select="tag:foo")
    """

    def __init__(
        self,
        manifest: DbtManifest,
        select: str = "fqn:*",
        exclude: Optional[str] = None,
    ) -> None:
        self.manifest = check.inst_param(manifest, "manifest", DbtManifest)
        self.select = check.str_param(select, "select")
        self.exclude = check.opt_str_param(exclude, "exclude", default="")

    def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
        dbt_nodes = self.manifest.node_info_by_dbt_unique_id

        keys = set()
        for unique_id in select_unique_ids_from_manifest(
            select=self.select,
            exclude=self.exclude,
            manifest_json=self.manifest.raw_manifest,
        ):
            node_info = dbt_nodes[unique_id]
            is_dbt_asset = node_info["resource_type"] in ASSET_RESOURCE_TYPES
            if is_dbt_asset and not is_non_asset_node(node_info):
                asset_key = self.manifest.node_info_to_asset_key(node_info)
                keys.add(asset_key)

        return keys


@dataclass
class DbtCliEventMessage:
    """The representation of a dbt CLI event.

    Args:
        raw_event (Dict[str, Any]): The raw event dictionary.
            See https://docs.getdbt.com/reference/events-logging#structured-logging for more
            information.
    """

    raw_event: Dict[str, Any]

    @classmethod
    def from_log(cls, log: str) -> "DbtCliEventMessage":
        """Parse an event according to https://docs.getdbt.com/reference/events-logging#structured-logging.

        We assume that the log format is json.
        """
        raw_event: Dict[str, Any] = json.loads(log)

        return cls(raw_event=raw_event)

    def __str__(self) -> str:
        return self.raw_event["info"]["msg"]

    def to_default_asset_events(
        self, manifest: DbtManifest
    ) -> Iterator[Union[Output, AssetObservation]]:
        """Convert a dbt CLI event to a set of corresponding Dagster events.

        Args:
            manifest (DbtManifest): The dbt manifest wrapper.

        Returns:
            Iterator[Union[Output, AssetObservation]]: A set of corresponding Dagster events.
                - AssetMaterializations for refables (e.g. models, seeds, snapshots.)
                - AssetObservations for test results.
        """
        event_node_info: Dict[str, Any] = self.raw_event["data"].get("node_info")
        if not event_node_info:
            return

        unique_id: str = event_node_info["unique_id"]
        node_resource_type: str = event_node_info["resource_type"]
        node_status: str = event_node_info["node_status"]

        is_node_successful = node_status == NodeStatus.Success
        is_node_finished = bool(event_node_info.get("node_finished_at"))
        if node_resource_type in NodeType.refable() and is_node_successful:
            started_at = dateutil.parser.isoparse(event_node_info["node_started_at"])
            finished_at = dateutil.parser.isoparse(event_node_info["node_finished_at"])
            duration_seconds = (finished_at - started_at).total_seconds()

            yield Output(
                value=None,
                output_name=output_name_fn(event_node_info),
                metadata={
                    "unique_id": unique_id,
                    "Execution Duration": duration_seconds,
                },
            )
        elif node_resource_type == NodeType.Test and is_node_finished:
            upstream_unique_ids: List[str] = manifest.raw_manifest["parent_map"][unique_id]

            for upstream_unique_id in upstream_unique_ids:
                upstream_node_info: Dict[str, Any] = manifest.raw_manifest["nodes"].get(
                    upstream_unique_id
                ) or manifest.raw_manifest["sources"].get(upstream_unique_id)
                upstream_asset_key = manifest.node_info_to_asset_key(upstream_node_info)

                yield AssetObservation(
                    asset_key=upstream_asset_key,
                    metadata={
                        "unique_id": unique_id,
                        "status": node_status,
                    },
                )


@dataclass
class DbtCliInvocation:
    """The representation of an invoked dbt command.

    Args:
        process (subprocess.Popen): The process running the dbt command.
        manifest (DbtManifest): The dbt manifest wrapper.
        project_dir (Path): The path to the dbt project.
        target_path (Path): The path to the dbt target folder.
        raise_on_error (bool): Whether to raise an exception if the dbt command fails.
    """

    process: subprocess.Popen
    manifest: DbtManifest
    project_dir: Path
    target_path: Path
    raise_on_error: bool

    @classmethod
    def run(
        cls,
        args: List[str],
        env: Dict[str, str],
        manifest: DbtManifest,
        project_dir: Path,
        target_path: Path,
        raise_on_error: bool,
    ) -> "DbtCliInvocation":
        # Attempt to take advantage of partial parsing. If there is a `partial_parse.msgpack` in
        # in the target folder, then copy it to the dynamic target path.
        #
        # This effectively allows us to skip the parsing of the manifest, which can be expensive.
        # See https://docs.getdbt.com/reference/programmatic-invocations#reusing-objects for more
        # details.
        partial_parse_file_path = project_dir.joinpath("target", PARTIAL_PARSE_FILE_NAME)
        partial_parse_destination_target_path = target_path.joinpath(PARTIAL_PARSE_FILE_NAME)

        if partial_parse_file_path.exists():
            logger.info(
                f"Copying `{partial_parse_file_path}` to `{partial_parse_destination_target_path}`"
                " to take advantage of partial parsing."
            )

            partial_parse_destination_target_path.parent.mkdir(parents=True)
            shutil.copy(partial_parse_file_path, partial_parse_destination_target_path)

        # Create a subprocess that runs the dbt CLI command.
        logger.info(f"Running dbt command: `{' '.join(args)}`.")
        process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=project_dir,
        )

        return cls(
            process=process,
            manifest=manifest,
            project_dir=project_dir,
            target_path=target_path,
            raise_on_error=raise_on_error,
        )

    def wait(self) -> Sequence[DbtCliEventMessage]:
        """Wait for the dbt CLI process to complete and return the events.

        Returns:
            Sequence[DbtCliEventMessage]: A sequence of events from the dbt CLI process.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCli, DbtManifest

                manifest = DbtManifest.read(path="path/to/manifest.json")
                dbt = DbtCli(project_dir="/path/to/dbt/project")

                dbt_cli_task = dbt.cli(["run"], manifest=manifest)

                dbt_cli_task.wait()
        """
        return list(self.stream_raw_events())

    def is_successful(self) -> bool:
        """Return whether the dbt CLI process completed successfully.

        Returns:
            bool: True, if the dbt CLI process returns with a zero exit code, and False otherwise.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCli, DbtManifest

                manifest = DbtManifest.read(path="path/to/manifest.json")
                dbt = DbtCli(project_dir="/path/to/dbt/project")

                dbt_cli_task = dbt.cli(["run"], manifest=manifest)

                if dbt_cli_task.is_successful():
                    ...
        """
        return self.process.wait() == 0

    def stream(self) -> Iterator[Union[Output, AssetObservation]]:
        """Stream the events from the dbt CLI process and convert them to Dagster events.

        Returns:
            Iterator[Union[Output, AssetObservation]]: A set of corresponding Dagster events.
                - Output for refables (e.g. models, seeds, snapshots.)
                - AssetObservations for test results.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCli, DbtManifest, dbt_assets

                manifest = DbtManifest.read(path="target/manifest.json")


                @dbt_assets(manifest=manifest)
                def my_dbt_assets(dbt: DbtCli):
                    yield from dbt.cli(["run"], manifest=manifest).stream()
        """
        for event in self.stream_raw_events():
            yield from event.to_default_asset_events(manifest=self.manifest)

    def stream_raw_events(self) -> Iterator[DbtCliEventMessage]:
        """Stream the events from the dbt CLI process.

        Returns:
            Iterator[DbtCliEventMessage]: An iterator of events from the dbt CLI process.
        """
        for raw_line in self.process.stdout or []:
            log: str = raw_line.decode().strip()
            try:
                event = DbtCliEventMessage.from_log(log=log)

                # Re-emit the logs from dbt CLI process into stdout.
                sys.stdout.write(str(event) + "\n")
                sys.stdout.flush()

                yield event
            except:
                # If we can't parse the log, then just emit it as a raw log.
                sys.stdout.write(log + "\n")
                sys.stdout.flush()

        # Ensure that the dbt CLI process has completed.
        if not self.is_successful() and self.raise_on_error:
            raise DagsterDbtCliRuntimeError(
                description=(
                    f"The dbt CLI process failed with exit code {self.process.returncode}. Check"
                    " the compute logs for the full information about the error."
                )
            )

    def get_artifact(
        self,
        artifact: Union[
            Literal["manifest.json"],
            Literal["catalog.json"],
            Literal["run_results.json"],
            Literal["sources.json"],
        ],
    ) -> Dict[str, Any]:
        """Retrieve a dbt artifact from the target path.

        See https://docs.getdbt.com/reference/artifacts/dbt-artifacts for more information.

        Args:
            artifact (Union[Literal["manifest.json"], Literal["catalog.json"], Literal["run_results.json"], Literal["sources.json"]]): The name of the artifact to retrieve.

        Returns:
            Dict[str, Any]: The artifact as a dictionary.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCli, DbtManifest

                manifest = DbtManifest.read(path="path/to/manifest.json")
                dbt = DbtCli(project_dir="/path/to/dbt/project")

                dbt_cli_task = dbt.cli(["run"], manifest=manifest)
                dbt_cli_task.wait()

                # Retrieve the run_results.json artifact.
                if dbt_cli_task.is_successful():
                    run_results = dbt_cli_task.get_artifact("run_results.json")
        """
        artifact_path = self.target_path.joinpath(artifact)
        with artifact_path.open() as handle:
            return json.loads(handle.read())


class DbtCli(ConfigurableResource):
    """A resource used to execute dbt CLI commands.

    Attributes:
        project_dir (str): The path to the dbt project directory. This directory should contain a
            `dbt_project.yml`. See https://docs.getdbt.com/reference/dbt_project.yml for more
            information.
        global_config_flags (List[str]): A list of global flags configuration to pass to the dbt CLI
            invocation. See https://docs.getdbt.com/reference/global-configs for a full list of
            configuration.
        profile (Optional[str]): The profile from your dbt `profiles.yml` to use for execution. See
            https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        target (Optional[str]): The target from your dbt `profiles.yml` to use for execution. See
            https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.

    Examples:
        .. code-block:: python

            from dagster_dbt import DbtCli

            dbt = DbtCli(
                project_dir="/path/to/dbt/project",
                global_config_flags=["--no-use-colors"],
                profile="jaffle_shop",
                target="dev",
            )
    """

    project_dir: str = Field(
        ...,
        description=(
            "The path to your dbt project directory. This directory should contain a"
            " `dbt_project.yml`. See https://docs.getdbt.com/reference/dbt_project.yml for more"
            " information."
        ),
    )
    global_config_flags: List[str] = Field(
        default=[],
        description=(
            "A list of global flags configuration to pass to the dbt CLI invocation. See"
            " https://docs.getdbt.com/reference/global-configs for a full list of configuration."
        ),
    )
    profile: Optional[str] = Field(
        default=None,
        description=(
            "The profile from your dbt `profiles.yml` to use for execution. See"
            " https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more"
            " information."
        ),
    )
    target: Optional[str] = Field(
        default=None,
        description=(
            "The target from your dbt `profiles.yml` to use for execution. See"
            " https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more"
            " information."
        ),
    )

    def _get_unique_target_path(self, *, context: Optional[OpExecutionContext]) -> str:
        """Get a unique target path for the dbt CLI invocation.

        Args:
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            str: A unique target path for the dbt CLI invocation.
        """
        current_unix_timestamp = str(int(time.time()))
        path = current_unix_timestamp
        if context:
            path = f"{context.op.name}-{context.run_id[:7]}-{current_unix_timestamp}"

        return f"target/{path}"

    def cli(
        self,
        args: List[str],
        *,
        raise_on_error: bool = True,
        manifest: DbtManifest,
        context: Optional[OpExecutionContext] = None,
    ) -> DbtCliInvocation:
        """Execute a dbt command.

        Args:
            args (List[str]): The dbt CLI command to execute.
            raise_on_error (bool): Whether to raise an exception if the dbt CLI command fails.
            manifest (DbtManifest): The dbt manifest wrapper.
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            DbtCliInvocation: A task that can be used to retrieve the output of the dbt CLI command.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCli, DbtManifest, dbt_assets

                manifest = DbtManifest.read(path="target/manifest.json")


                @dbt_assets(manifest=manifest)
                def my_dbt_assets(dbt: DbtCli):
                    yield from dbt.cli(["run"], manifest=manifest).stream()
        """
        target_path = self._get_unique_target_path(context=context)
        env = {
            **os.environ.copy(),
            # Run dbt with unbuffered output.
            "PYTHONUNBUFFERED": "1",
            # The DBT_LOG_FORMAT environment variable must be set to `json`. We use this
            # environment variable to ensure that the dbt CLI outputs structured logs.
            "DBT_LOG_FORMAT": "json",
            # The DBT_TARGET_PATH environment variable is set to a unique value for each dbt
            # invocation so that artifact paths are separated.
            # See https://discourse.getdbt.com/t/multiple-run-results-json-and-manifest-json-files/7555
            # for more information.
            "DBT_TARGET_PATH": target_path,
        }

        # TODO: verify that args does not have any selection flags if the context and manifest
        # are passed to this function.
        selection_args: List[str] = []
        if context and manifest:
            logger.info(
                "A context and manifest were provided to the dbt CLI client. Selection arguments to"
                " dbt will automatically be interpreted from the execution environment."
            )

            selection_args = manifest.get_subset_selection_for_context(
                context=context,
                select=context.op.tags.get("dagster-dbt/select"),
                exclude=context.op.tags.get("dagster-dbt/exclude"),
            )

        profile_args: List[str] = []
        if self.profile:
            profile_args = ["--profile", self.profile]

        if self.target:
            profile_args += ["--target", self.target]

        args = ["dbt"] + self.global_config_flags + args + profile_args + selection_args
        project_dir = Path(self.project_dir).resolve(strict=True)

        return DbtCliInvocation.run(
            args=args,
            env=env,
            manifest=manifest,
            project_dir=project_dir,
            target_path=project_dir.joinpath(target_path),
            raise_on_error=raise_on_error,
        )
