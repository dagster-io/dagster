import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Union

from dagster import (
    AssetKey,
    AssetObservation,
    ConfigurableResource,
    OpExecutionContext,
    Output,
    get_dagster_logger,
)
from dagster._annotations import experimental
from dbt.contracts.results import NodeStatus
from dbt.node_types import NodeType
from pydantic import Field
from typing_extensions import Literal

from ..asset_utils import default_asset_key_fn, output_name_fn

logger = get_dagster_logger()


@dataclass
class DbtManifest:
    """Helper class for dbt manifest operations."""

    raw_manifest: Dict[str, Any]

    @classmethod
    def read(cls, path: str) -> "DbtManifest":
        """Read the file path to a dbt manifest and create a DbtManifest object.

        Args:
            path(str): The path to the dbt manifest.json file.

        Returns:
            DbtManifest: A DbtManifest object.
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
        return default_asset_key_fn(node_info)

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

    def get_node_info_by_output_name(self, output_name: str) -> Mapping[str, Any]:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.node_info_by_output_name[output_name]

    def get_node_info_by_asset_key(self, asset_key: AssetKey) -> Mapping[str, Any]:
        """Get a dbt node's dictionary representation in the manifest by its Dagster output name."""
        return self.node_info_by_asset_key[asset_key]

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
            node_info = self.get_node_info_by_output_name(output_name)

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


@dataclass
class DbtCliEventMessage:
    """Represents a dbt CLI event."""

    event: Dict[str, Any]

    @classmethod
    def from_log(cls, log: str) -> "DbtCliEventMessage":
        """Parse an event according to https://docs.getdbt.com/reference/events-logging#structured-logging.

        We assume that the log format is json.
        """
        event: Dict[str, Any] = json.loads(log)

        return cls(event=event)

    def __str__(self) -> str:
        return self.event["info"]["msg"]

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
        event_node_info: Dict[str, Any] = self.event["data"].get("node_info")
        if not event_node_info:
            return

        unique_id: str = event_node_info["unique_id"]
        node_resource_type: str = event_node_info["resource_type"]
        node_status: str = event_node_info["node_status"]

        is_node_successful = node_status == NodeStatus.Success
        is_node_finished = bool(event_node_info.get("node_finished_at"))
        if node_resource_type in NodeType.refable() and is_node_successful:
            yield Output(
                value=None,
                output_name=output_name_fn(event_node_info),
                metadata={
                    "unique_id": unique_id,
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
class DbtCliTask:
    process: subprocess.Popen
    manifest: DbtManifest
    project_dir: str
    target_path: str

    def wait(self) -> Sequence[DbtCliEventMessage]:
        """Wait for the dbt CLI process to complete and return the events.

        Returns:
            Sequence[DbtCliEventMessage]: A sequence of events from the dbt CLI process.
        """
        return list(self.stream_raw_events())

    def stream(self) -> Iterator[Union[Output, AssetObservation]]:
        """Stream the events from the dbt CLI process and convert them to Dagster events.

        Returns:
            Iterator[Union[Output, AssetObservation]]: A set of corresponding Dagster events.
                - AssetMaterializations for refables (e.g. models, seeds, snapshots.)
                - AssetObservations for test results.
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
            event = DbtCliEventMessage.from_log(log=log)

            # Re-emit the logs from dbt CLI process into stdout.
            sys.stdout.write(str(event) + "\n")
            sys.stdout.flush()

            yield event

        # TODO: handle the return codes here!
        # https://docs.getdbt.com/reference/exit-codes
        return_code = self.process.wait()

        return return_code

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

        See https://docs.getdbt.com/reference/artifacts/dbt-artifacts.

        Args:
            artifact (Union[Literal["manifest.json"], Literal["catalog.json"], Literal["run_results.json"], Literal["sources.json"]]): The name of the artifact to retrieve.

        Returns:
            Dict[str, Any]: The artifact as a dictionary.
        """
        artifact_path = os.path.join(self.project_dir, self.target_path, artifact)
        with open(artifact_path) as handle:
            return json.loads(handle.read())


@experimental
class DbtCli(ConfigurableResource):
    """A resource that can be used to execute dbt CLI commands."""

    project_dir: str = Field(
        ...,
        description=(
            "The path to your dbt project directory. This directory should contain a"
            " `dbt_project.yml`. https://docs.getdbt.com/reference/dbt_project.yml for more"
            " information."
        ),
    )
    global_config: List[str] = Field(
        default=[],
        description=(
            "A list of global flags configuration to pass to the dbt CLI invocation. See"
            " https://docs.getdbt.com/reference/global-configs for a full list of configuration."
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
        manifest: DbtManifest,
        context: Optional[OpExecutionContext] = None,
    ) -> DbtCliTask:
        """Execute a dbt command.

        Args:
            args (List[str]): The dbt CLI command to execute.
            manifest (DbtManifest): The dbt manifest wrapper.
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            DbtCliTask: A task that can be used to retrieve the output of the dbt CLI command.

        Examples:
            .. code-block:: python

                from dagster_dbt.asset_decorator import dbt_assets
                from dagster_dbt.cli import DbtCli, DbtManifest

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
            # See: https://discourse.getdbt.com/t/multiple-run-results-json-and-manifest-json-files/7555
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

        args = ["dbt"] + self.global_config + args + selection_args
        logger.info(f"Running dbt command: `{' '.join(args)}`.")

        # Create a subprocess that runs the dbt CLI command.
        process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=self.project_dir,
        )

        return DbtCliTask(
            process=process,
            manifest=manifest,
            project_dir=self.project_dir,
            target_path=target_path,
        )
