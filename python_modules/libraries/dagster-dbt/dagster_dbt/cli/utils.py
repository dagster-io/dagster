import json
import os
import subprocess
from typing import Any, Iterator, List, Mapping, Optional, Sequence, Tuple, Union

import dagster._check as check
import dateutil
from dagster._core.definitions.events import AssetObservation, Output
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.utils import coerce_valid_log_level

from ..errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
)
from ..utils import ASSET_RESOURCE_TYPES, _get_output_name
from .constants import DBT_RUN_RESULTS_COMMANDS, DEFAULT_DBT_TARGET_PATH
from .types import DbtCliOutput


def _create_command_list(
    executable: str,
    warn_error: bool,
    json_log_format: bool,
    command: str,
    flags_dict: Mapping[str, Any],
) -> Sequence[str]:
    prefix = [executable]
    if warn_error:
        prefix += ["--warn-error"]
    if json_log_format:
        prefix += ["--no-use-color", "--log-format", "json"]

    full_command = command.split(" ")
    for flag, value in flags_dict.items():
        if not value:
            continue

        full_command.append(f"--{flag}")

        if isinstance(value, bool):
            pass
        elif isinstance(value, list):
            check.list_param(value, f"config.{flag}", of_type=str)
            full_command += value
        elif isinstance(value, dict):
            full_command.append(json.dumps(value))
        else:
            full_command.append(str(value))

    return prefix + full_command


def _process_line(
    line: str, log: Any, json_log_format: bool, capture_logs: bool
) -> Tuple[str, Optional[Mapping[str, Any]]]:
    """Processes a line of output from the dbt CLI."""
    log_level = "info"

    message = line
    json_line = None

    if json_log_format:
        try:
            json_line = json.loads(line)
        except json.JSONDecodeError:
            pass
        else:
            # in rare cases, the loaded json line may be a string rather than a dictionary
            if isinstance(json_line, dict):
                message = json_line.get(
                    # Attempt to get the message from the dbt-core==1.3.* format
                    "msg",
                    # Otherwise, try to get the message from the dbt-core==1.4.* format
                    json_line.get("info", {}).get(
                        "msg",
                        # If all else fails, default to the whole line
                        message,
                    ),
                )
                log_level = json_line.get(
                    # Attempt to get the log level from the dbt-core==1.3.* format
                    "level",
                    # Otherwise, try to get the message from the dbt-core==1.4.* format
                    json_line.get("info", {}).get(
                        "level",
                        # If all else fails, default to the `debug` level
                        "debug",
                    ),
                )
    elif "Done." not in line:
        # attempt to parse a log level out of the line
        if "ERROR" in line:
            log_level = "error"
        elif "WARN" in line:
            log_level = "warn"

    if capture_logs:
        log.log(coerce_valid_log_level(log_level), message)

    return message, json_line


def _cleanup_process(process, messages, log, ignore_handled_error: bool) -> int:
    process.wait()
    return_code = process.returncode

    log.info("dbt exited with return code {return_code}".format(return_code=return_code))

    if return_code == 2:
        raise DagsterDbtCliFatalRuntimeError(messages=messages)

    if return_code == 1 and not ignore_handled_error:
        raise DagsterDbtCliHandledRuntimeError(messages=messages)

    return return_code


def execute_cli(
    executable: str,
    command: str,
    flags_dict: Mapping[str, Any],
    log: Any,
    warn_error: bool,
    ignore_handled_error: bool,
    target_path: str,
    docs_url: Optional[str] = None,
    json_log_format: bool = True,
    capture_logs: bool = True,
) -> DbtCliOutput:
    """Executes a command on the dbt CLI in a subprocess."""
    try:
        import dbt  # noqa: F401
    except ImportError as e:
        raise check.CheckError(
            "You must have `dbt-core` installed in order to execute dbt CLI commands."
        ) from e

    check.str_param(executable, "executable")
    check.str_param(command, "command")
    check.mapping_param(flags_dict, "flags_dict", key_type=str)
    check.bool_param(warn_error, "warn_error")
    check.bool_param(ignore_handled_error, "ignore_handled_error")
    check.bool_param(capture_logs, "capture_logs")

    command_list = _create_command_list(
        executable=executable,
        warn_error=warn_error,
        json_log_format=json_log_format,
        command=command,
        flags_dict=flags_dict,
    )

    # Execute the dbt CLI command in a subprocess.
    full_command = " ".join(command_list)
    log.info(f"Executing command: {' '.join(command_list)}")

    # Collect the output of the dbt CLI command in different formats
    lines: List[str] = []
    messages: List[str] = []
    json_lines: List[Mapping[str, Any]] = []

    process = subprocess.Popen(
        command_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for raw_line in process.stdout or []:
        line = _decode(raw_line)

        message, json_line = _process_line(line, log, json_log_format, capture_logs)
        lines.append(line)
        messages.append(message)
        if json_line is not None:
            json_lines.append(json_line)

    return_code = _cleanup_process(process, messages, log, ignore_handled_error)

    run_results = (
        parse_run_results(flags_dict["project-dir"], target_path)
        if command in DBT_RUN_RESULTS_COMMANDS
        else {}
    )

    return DbtCliOutput(
        command=full_command,
        return_code=return_code,
        raw_output="\n\n".join(lines),
        logs=json_lines,
        result=run_results,
        docs_url=docs_url,
    )


def parse_run_results(path: str, target_path: str = DEFAULT_DBT_TARGET_PATH) -> Mapping[str, Any]:
    """Parses the `target/run_results.json` artifact that is produced by a dbt process."""
    run_results_path = os.path.join(path, target_path, "run_results.json")
    try:
        with open(run_results_path, "rb") as file:
            bs = file.read()
            print("FILE BYTES:", bs)
            return json.loads(bs)
    except FileNotFoundError:
        raise DagsterDbtCliOutputsNotFoundError(path=run_results_path)


def remove_run_results(path: str, target_path: str = DEFAULT_DBT_TARGET_PATH):
    """Parses the `target/run_results.json` artifact that is produced by a dbt process."""
    run_results_path = os.path.join(path, target_path, "run_results.json")
    if os.path.exists(run_results_path):
        os.remove(run_results_path)


def parse_manifest(path: str, target_path: str = DEFAULT_DBT_TARGET_PATH) -> Mapping[str, Any]:
    """Parses the `target/manifest.json` artifact that is produced by a dbt process."""
    manifest_path = os.path.join(path, target_path, "manifest.json")
    try:
        with open(manifest_path) as file:
            return json.load(file)
    except FileNotFoundError:
        raise DagsterDbtCliOutputsNotFoundError(path=manifest_path)


def _events_for_structured_json_line(
    json_line: Mapping[str, Any],
    manifest_json,
    node_info_to_asset_key,
    context: OpExecutionContext,
    runtime_metadata_fn,
) -> Iterator[Union[AssetObservation, Output]]:
    """Parses a json line into a Dagster event. Attempts to replicate the behavior of result_to_events
    as closely as possible.
    """
    runtime_node_info = json_line.get("data", {}).get("node_info", {})
    if not runtime_node_info:
        return

    node_resource_type = runtime_node_info.get("resource_type")
    node_status = runtime_node_info.get("node_status")
    unique_id = runtime_node_info.get("unique_id")

    if not node_resource_type or not unique_id:
        return

    compiled_node_info = manifest_json["nodes"][unique_id]

    if node_resource_type in ASSET_RESOURCE_TYPES and node_status == "success":
        metadata = runtime_metadata_fn(context, compiled_node_info) if runtime_metadata_fn else {}
        started_at_str = runtime_node_info.get("node_started_at")
        finished_at_str = runtime_node_info.get("node_finished_at")
        if started_at_str is None or finished_at_str is None:
            return

        started_at = dateutil.parser.isoparse(started_at_str)  # type: ignore
        completed_at = dateutil.parser.isoparse(finished_at_str)  # type: ignore
        duration = completed_at - started_at
        metadata.update(
            {
                "Execution Started At": started_at.isoformat(timespec="seconds"),
                "Execution Completed At": completed_at.isoformat(timespec="seconds"),
                "Execution Duration": duration.total_seconds(),
            }
        )
        yield Output(
            value=None,
            output_name=_get_output_name(compiled_node_info),
            metadata=metadata,
        )
    elif node_resource_type == "test" and runtime_node_info.get("node_finished_at") is not None:
        upstream_unique_ids = (
            manifest_json["nodes"][unique_id].get("depends_on", {}).get("nodes", [])
        )
        # tests can apply to multiple asset keys
        for upstream_id in upstream_unique_ids:
            # the upstream id can reference a node or a source
            upstream_node_info = manifest_json["nodes"].get(upstream_id) or manifest_json[
                "sources"
            ].get(upstream_id)
            if upstream_node_info is None:
                continue
            upstream_asset_key = node_info_to_asset_key(upstream_node_info)
            yield AssetObservation(
                asset_key=upstream_asset_key,
                metadata={
                    "Test ID": unique_id,
                    "Test Status": node_status,
                },
            )


def execute_cli_event_generator(
    executable: str,
    command: str,
    flags_dict: Mapping[str, Any],
    log: Any,
    warn_error: bool,
    ignore_handled_error: bool,
    json_log_format: bool,
    capture_logs: bool,
    manifest_json: Mapping[str, Any],
    node_info_to_asset_key,
    context: OpExecutionContext,
    runtime_metadata_fn,
) -> Iterator[Union[AssetObservation, Output]]:
    if not json_log_format:
        check.failed("Cannot stream events from dbt output if json_log_format is False.")

    command_list = _create_command_list(
        executable=executable,
        warn_error=warn_error,
        json_log_format=json_log_format,
        command=command,
        flags_dict=flags_dict,
    )

    messages: List[str] = []
    process = subprocess.Popen(
        command_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for raw_line in process.stdout or []:
        print("--" * 40)
        print("bytes:", raw_line)
        print(".." * 40)
        line = _decode(raw_line)
        message, json_line = _process_line(line, log, json_log_format, capture_logs)
        messages.append(message)
        if json_line is not None:
            yield from _events_for_structured_json_line(
                json_line, manifest_json, node_info_to_asset_key, context, runtime_metadata_fn
            )

    _cleanup_process(process, messages, log, ignore_handled_error)


def _decode(raw_line: bytes) -> str:
    s = raw_line.decode("utf-8")
    print("string:", s)
    print("~~" * 40)
    return raw_line.decode("utf-8").rstrip()
    try:
        return raw_line.decode("utf-8").strip()
    except:
        return raw_line.decode("latin1").strip()
