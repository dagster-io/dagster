import json
import os
import subprocess
from typing import Any, Mapping, Optional, Sequence

import dagster._check as check
from dagster._core.utils import coerce_valid_log_level

from ..errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
)
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

    return_code = 0

    # raw lines
    raw_output = []

    # parsed messages from the log output
    messages = []

    # json dictionaries for each line (if applicable)
    json_lines = []

    process = subprocess.Popen(
        command_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for raw_line in process.stdout or []:
        line = raw_line.decode("utf-8").rstrip()

        log_level = "info"
        message = line
        raw_output.append(line)

        if json_log_format:
            try:
                json_line = json.loads(line)
                json_lines.append(json_line)
            except json.JSONDecodeError:
                pass
            else:
                # in rare cases, the loaded json line may be a string rather than a dictionary
                if isinstance(json_line, dict):
                    message = json_line.get("message", json_line.get("msg", message))
                    log_level = json_line.get("levelname", json_line.get("level", "debug"))
        elif "Done." not in line:
            # attempt to parse a log level out of the line
            if "ERROR" in line:
                log_level = "error"
            elif "WARN" in line:
                log_level = "warn"

        messages.append(message)
        if capture_logs:
            log.log(coerce_valid_log_level(log_level), message)

    process.wait()
    return_code = process.returncode

    log.info("dbt exited with return code {return_code}".format(return_code=return_code))

    raw_output = "\n\n".join(raw_output)

    if return_code == 2:
        raise DagsterDbtCliFatalRuntimeError(messages=messages)

    if return_code == 1 and not ignore_handled_error:
        raise DagsterDbtCliHandledRuntimeError(messages=messages)

    run_results = (
        parse_run_results(flags_dict["project-dir"], target_path)
        if command in DBT_RUN_RESULTS_COMMANDS
        else {}
    )

    return DbtCliOutput(
        command=full_command,
        return_code=return_code,
        raw_output=raw_output,
        logs=json_lines,
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
