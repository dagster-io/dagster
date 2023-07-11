import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import (
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
    AssetObservation,
    ConfigurableResource,
    OpExecutionContext,
    Output,
    _check as check,
    get_dagster_logger,
)
from dbt.contracts.results import NodeStatus
from dbt.node_types import NodeType
from pydantic import Field
from typing_extensions import Literal

from ..asset_utils import output_name_fn
from ..dagster_dbt_translator import DagsterDbtTranslator
from ..errors import DagsterDbtCliRuntimeError

logger = get_dagster_logger()


PARTIAL_PARSE_FILE_NAME = "partial_parse.msgpack"


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
        self,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
    ) -> Iterator[Union[Output, AssetObservation]]:
        """Convert a dbt CLI event to a set of corresponding Dagster events.

        Args:
            manifest (Mapping[str, Any]): The dbt manifest blob.
            dagster_dbt_translator (DagsterDbtTranslator): Optionally, a custom translator for
                linking dbt nodes to Dagster assets.

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
            upstream_unique_ids: List[str] = manifest["parent_map"][unique_id]

            for upstream_unique_id in upstream_unique_ids:
                upstream_node_info: Dict[str, Any] = manifest["nodes"].get(
                    upstream_unique_id
                ) or manifest["sources"].get(upstream_unique_id)
                upstream_asset_key = dagster_dbt_translator.node_info_to_asset_key(
                    upstream_node_info
                )

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
        manifest (Mapping[str, Any]): The dbt manifest blob.
        project_dir (Path): The path to the dbt project.
        target_path (Path): The path to the dbt target folder.
        raise_on_error (bool): Whether to raise an exception if the dbt command fails.
    """

    process: subprocess.Popen
    manifest: Mapping[str, Any]
    dagster_dbt_translator: DagsterDbtTranslator
    project_dir: Path
    target_path: Path
    raise_on_error: bool

    @classmethod
    def run(
        cls,
        args: List[str],
        env: Dict[str, str],
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
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
            dagster_dbt_translator=dagster_dbt_translator,
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

                import json
                from dagster_dbt import DbtCli

                with open("path/to/manifest.json", "r") as f:
                    manifest = json.load(f)

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

                import json
                from dagster_dbt import DbtCli

                with open("path/to/manifest.json", "r") as f:
                    manifest = json.load(f)

                dbt = DbtCli(project_dir="/path/to/dbt/project")

                dbt_cli_task = dbt.cli(["run"], manifest=manifest)
                dbt_cli_task.wait()

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

                from pathlib import Path
                from dagster_dbt import DbtCli, dbt_assets

                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context, dbt: DbtCli):
                    yield from dbt.cli(["run"], context=context).stream()
        """
        for event in self.stream_raw_events():
            yield from event.to_default_asset_events(
                manifest=self.manifest, dagster_dbt_translator=self.dagster_dbt_translator
            )

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

                import json
                from dagster_dbt import DbtCli

                with open("path/to/manifest.json", "r") as f:
                    manifest = json.load(f)

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
        manifest: Optional[Mapping[str, Any]] = None,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        context: Optional[OpExecutionContext] = None,
    ) -> DbtCliInvocation:
        """Execute a dbt command.

        Args:
            args (List[str]): The dbt CLI command to execute.
            raise_on_error (bool): Whether to raise an exception if the dbt CLI command fails.
            manifest (Optional[Mapping[str, Any]]): The dbt manifest blob. If an execution context
                from within `@dbt_assets` is provided to the context argument, then the manifest
                provided to `@dbt_assets` will be used.
            dagster_dbt_translator (Optional[DagsterDbtTranslator]): The translator to link dbt
                nodes to Dagster assets. If an execution context from within `@dbt_assets` is
                provided to the context argument, then the dagster_dbt_translator provided to
                `@dbt_assets` will be used.
            context (Optional[OpExecutionContext]): The execution context from within `@dbt_assets`.

        Returns:
            DbtCliInvocation: A task that can be used to retrieve the output of the dbt CLI command.

        Examples:
            .. code-block:: python

                from pathlib import Path
                from dagster_dbt import DbtCli, dbt_assets

                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context, dbt: DbtCli):
                    yield from dbt.cli(["run"], context=context).stream()
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

        from dagster_dbt.dbt_assets_definition import DbtAssetsDefinition

        if context and context.assets_def and isinstance(context.assets_def, DbtAssetsDefinition):
            dbt_assets_def = context.assets_def

            logger.info(
                "A DbtAssetsDefinition was provided to the dbt CLI client. Selection arguments to"
                " dbt will automatically be interpreted from the execution environment."
            )

            selection_args = dbt_assets_def.get_subset_selection_for_context(
                context=context,
                select=context.op.tags.get("dagster-dbt/select"),
                exclude=context.op.tags.get("dagster-dbt/exclude"),
            )
            manifest = dbt_assets_def.manifest
            dagster_dbt_translator = dbt_assets_def.dagster_dbt_translator
        else:
            selection_args: List[str] = []
            dbt_assets_def = None
            if manifest is None:
                check.failed(
                    "Must provide a value for the manifest argument if not executing as part of"
                    " @dbt_assets"
                )
            dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

        # TODO: verify that args does not have any selection flags if the context and manifest
        # are passed to this function.

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
            dagster_dbt_translator=dagster_dbt_translator,
            project_dir=project_dir,
            target_path=project_dir.joinpath(target_path),
            raise_on_error=raise_on_error,
        )
