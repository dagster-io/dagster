import json
import os
import subprocess
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, Iterator, List, Mapping, Sequence, Union

from dagster import (
    AssetKey,
    AssetObservation,
    ConfigurableResource,
    Output,
    get_dagster_logger,
)
from dbt.contracts.results import NodeStatus
from dbt.node_types import NodeType
from pydantic import Field

from ..asset_utils import default_asset_key_fn, output_name_fn

logger = get_dagster_logger()


@dataclass
class DbtManifest:
    """Helper class for dbt manifest operations."""

    raw_manifest: Dict[str, Any]

    @cached_property
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

    @cached_property
    def node_info_by_asset_key(self) -> Mapping[AssetKey, Mapping[str, Any]]:
        """A mapping of the default asset key for a dbt node to the node's dictionary representation in the manifest.
        """
        return {
            self.node_info_to_asset_key(node): node
            for node in self.node_info_by_dbt_unique_id.values()
        }

    @cached_property
    def node_info_by_output_name(self) -> Mapping[str, Mapping[str, Any]]:
        """A mapping of the default output name for a dbt node to the node's dictionary representation in the manifest.
        """
        return {output_name_fn(node): node for node in self.node_info_by_dbt_unique_id.values()}

    @cached_property
    def output_asset_key_replacements(self) -> Mapping[AssetKey, AssetKey]:
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


@dataclass
class DbtCliEventV2:
    """Represents a dbt CLI event."""

    event: Dict[str, Any]

    @classmethod
    def from_log(cls, log: str) -> "DbtCliEventV2":
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


class DbtCliTask:
    def __init__(self, process: subprocess.Popen) -> None:
        self._process = process

    def wait(self) -> Sequence[DbtCliEventV2]:
        """Wait for the dbt CLI process to complete and return the events.

        Returns:
            Sequence[DbtCliEventV2]: A sequence of events from the dbt CLI process.
        """
        return list(self.stream())

    def stream(self) -> Iterator[DbtCliEventV2]:
        """Stream the events from the dbt CLI process.

        Returns:
            Iterator[DbtCliEventV2]: An iterator of events from the dbt CLI process.
        """
        for raw_line in self._process.stdout or []:
            log: str = raw_line.decode().strip()
            event = DbtCliEventV2.from_log(log=log)

            yield event

        # TODO: handle the return codes here!
        # https://docs.getdbt.com/reference/exit-codes
        return_code = self._process.wait()

        return return_code


class DbtClientV2(ConfigurableResource):
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

    def cli(self, args: List[str]) -> DbtCliTask:
        """Execute a dbt command.

        Args:
            args (List[str]): The dbt CLI command to execute.

        Returns:
            DbtCliTask: A task that can be used to retrieve the output of the dbt CLI command.

        Examples:
            .. code-block:: python

                from dagster import op, ResourceParam
                from dagster_dbt import DbtClientV2

                @op
                def my_dbt_op(dbt: ResourceParam[DbtClientV2]):
                    events = dbt.cli(["run"]).wait()

                    for event in dbt.cli(["test"]).stream():
                        print(event)
        """
        # Run dbt with unbuffered output.
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # The DBT_LOG_FORMAT environment variable must be set to `json`. We use this
        # environment variable to ensure that the dbt CLI outputs structured logs.
        env["DBT_LOG_FORMAT"] = "json"

        args = ["dbt"] + self.global_config + args
        logger.info(f"Running dbt command: `{' '.join(args)}`.")

        # Create a subprocess that runs the dbt CLI command.
        process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=self.project_dir,
        )

        return DbtCliTask(process=process)
