import json
import os
import subprocess
from typing import Any, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster._core.utils import coerce_valid_log_level

from ..errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
)
from .types import DbtCliOutput

DEFAULT_DBT_TARGET_PATH = "target"

DBT_RUN_RESULTS_COMMANDS = ["run", "test", "seed", "snapshot", "docs generate", "build"]


class DbtCliEvent(NamedTuple):
    """Helper class to encapsulate parsed information from an active dbt CLI process."""

    line: Optional[str]
    message: Optional[str]
    parsed_json_line: Optional[Mapping[str, Any]]
    log_level: Optional[int]

    @classmethod
    def from_line(cls, line: str, json_log_format: bool) -> "DbtCliEvent":
        message = line
        parsed_json_line = None
        log_level = "info"

        # parse attributes out of json fields
        if json_log_format:
            try:
                parsed_json_line = json.loads(line)
            except json.JSONDecodeError:
                pass
            else:
                # in rare cases, the loaded json line may be a string rather than a dictionary
                if isinstance(parsed_json_line, dict):
                    message = parsed_json_line.get(
                        # Attempt to get the message from the dbt-core==1.3.* format
                        "msg",
                        # Otherwise, try to get the message from the dbt-core==1.4.* format
                        parsed_json_line.get("info", {}).get(
                            "msg",
                            # If all else fails, default to the whole line
                            line,
                        ),
                    )
                    log_level = parsed_json_line.get(
                        # Attempt to get the log level from the dbt-core==1.3.* format
                        "level",
                        # Otherwise, try to get the message from the dbt-core==1.4.* format
                        parsed_json_line.get("info", {}).get(
                            "level",
                            # If all else fails, default to the `debug` level
                            "debug",
                        ),
                    )
        # attempt to parse log level out of raw line
        elif "Done." not in line:
            # attempt to parse a log level out of the line
            if "ERROR" in line:
                log_level = "error"
            elif "WARN" in line:
                log_level = "warn"

        return DbtCliEvent(
            line=line,
            message=message,
            parsed_json_line=parsed_json_line,
            log_level=coerce_valid_log_level(log_level),
        )


def _create_command_list(
    executable: str,
    warn_error: bool,
    json_log_format: bool,
    command: str,
    flags_dict: Mapping[str, Any],
    debug: bool,
) -> Sequence[str]:
    prefix = [executable]
    if warn_error:
        prefix += ["--warn-error"]
    if json_log_format:
        prefix += ["--no-use-colors", "--log-format", "json"]
    if debug:
        prefix += ["--debug"]

    full_command = [*command.split(" "), *build_command_args_from_flags(flags_dict)]

    return prefix + full_command


def build_command_args_from_flags(flags_dict: Mapping[str, Any]) -> Sequence[str]:
    result = []
    for flag, value in flags_dict.items():
        if not value:
            continue

        result.append(f"--{flag}")

        if isinstance(value, bool):
            pass
        elif isinstance(value, list):
            check.list_param(value, f"config.{flag}", of_type=str)
            result += value
        elif isinstance(value, dict):
            result.append(json.dumps(value))
        else:
            result.append(str(value))

    return result


def _core_execute_cli(
    command_list: Sequence[str],
    ignore_handled_error: bool,
    json_log_format: bool,
    project_dir: str,
) -> Iterator[Union[DbtCliEvent, int]]:
    """Runs a dbt command in a subprocess and yields parsed output line by line."""
    # Execute the dbt CLI command in a subprocess.
    messages: List[str] = []

    # run dbt with unbuffered output
    passenv = os.environ.copy()
    passenv["PYTHONUNBUFFERED"] = "1"
    process = subprocess.Popen(
        command_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=passenv,
        cwd=project_dir if os.path.exists(project_dir) else None,
    )
    for raw_line in process.stdout or []:
        line = raw_line.decode().strip()

        cli_event = DbtCliEvent.from_line(line, json_log_format)

        if cli_event.message is not None:
            messages.append(cli_event.message)

        # yield the parsed values
        yield cli_event

    process.wait()
    return_code = process.returncode

    if return_code == 2:
        raise DagsterDbtCliFatalRuntimeError(messages=messages)

    if return_code == 1 and not ignore_handled_error:
        raise DagsterDbtCliHandledRuntimeError(messages=messages)

    yield return_code


def execute_cli_stream(
    executable: str,
    command: str,
    flags_dict: Mapping[str, Any],
    log: Any,
    warn_error: bool,
    ignore_handled_error: bool,
    json_log_format: bool = True,
    capture_logs: bool = True,
    debug: bool = False,
) -> Iterator[DbtCliEvent]:
    """Executes a command on the dbt CLI in a subprocess."""
    command_list = _create_command_list(
        executable=executable,
        warn_error=warn_error,
        json_log_format=json_log_format,
        command=command,
        flags_dict=flags_dict,
        debug=debug,
    )
    log.info(f"Executing command: {' '.join(command_list)}")

    for event in _core_execute_cli(
        command_list=command_list,
        json_log_format=json_log_format,
        ignore_handled_error=ignore_handled_error,
        project_dir=flags_dict["project-dir"],
    ):
        if isinstance(event, int):
            return_code = event
            log.info(f"dbt exited with return code {return_code}")
            break

        yield event
        if capture_logs:
            log.log(event.log_level, event.message)


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
    debug: bool = False,
) -> DbtCliOutput:
    """Executes a command on the dbt CLI in a subprocess."""
    check.str_param(executable, "executable")
    check.str_param(command, "command")
    check.mapping_param(flags_dict, "flags_dict", key_type=str)
    check.bool_param(warn_error, "warn_error")
    check.bool_param(ignore_handled_error, "ignore_handled_error")

    command_list = _create_command_list(
        executable=executable,
        warn_error=warn_error,
        json_log_format=json_log_format,
        command=command,
        flags_dict=flags_dict,
        debug=debug,
    )
    log.info(f"Executing command: {' '.join(command_list)}")

    return_code = 0
    lines, parsed_json_lines = [], []
    for event in _core_execute_cli(
        command_list=command_list,
        json_log_format=json_log_format,
        ignore_handled_error=ignore_handled_error,
        project_dir=flags_dict["project-dir"],
    ):
        if isinstance(event, int):
            return_code = event
            log.info(f"dbt exited with return code {return_code}")
            break

        if event.line is not None:
            lines.append(event.line)
        if event.parsed_json_line is not None:
            parsed_json_lines.append(event.parsed_json_line)

        if capture_logs:
            log.log(event.log_level, event.message)

    run_results = (
        parse_run_results(flags_dict["project-dir"], target_path)
        if command in DBT_RUN_RESULTS_COMMANDS
        else {}
    )

    return DbtCliOutput(
        command=" ".join(command_list),
        return_code=return_code,
        raw_output="\n\n".join(lines),
        logs=parsed_json_lines,
        result=run_results,
        docs_url=docs_url,
    )


def parse_run_results(path: str, target_path: str = DEFAULT_DBT_TARGET_PATH) -> Mapping[str, Any]:
    """Parses the `target/run_results.json` artifact that is produced by a dbt process."""
    run_results_path = os.path.join(path, target_path, "run_results.json")
    try:
        with open(run_results_path, encoding="utf8") as file:
            return json.load(file)
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
        with open(manifest_path, encoding="utf8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise DagsterDbtCliOutputsNotFoundError(path=manifest_path)
