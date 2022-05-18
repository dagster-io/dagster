import json
import os
import subprocess
from typing import Any, Dict, Optional

import dagster._check as check
from dagster.core.utils import coerce_valid_log_level

from ..errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
)
from .constants import DBT_RUN_RESULTS_COMMANDS, DEFAULT_DBT_TARGET_PATH
from .types import DbtCliOutput


def execute_cli(
    executable: str,
    command: str,
    flags_dict: Dict[str, Any],
    log: Any,
    warn_error: bool,
    ignore_handled_error: bool,
    target_path: str,
    docs_url: Optional[str] = None,
) -> DbtCliOutput:
    """Executes a command on the dbt CLI in a subprocess."""
    check.str_param(executable, "executable")
    check.str_param(command, "command")
    check.dict_param(flags_dict, "flags_dict", key_type=str)
    check.bool_param(warn_error, "warn_error")
    check.bool_param(ignore_handled_error, "ignore_handled_error")

    # Format the dbt CLI flags in the command..
    warn_error = ["--warn-error"] if warn_error else []
    command_list = [
        executable,
        "--no-use-color",
        "--log-format",
        "json",
        *warn_error,
        *command.split(" "),
    ]

    for flag, value in flags_dict.items():
        if not value:
            continue

        command_list.append(f"--{flag}")

        if isinstance(value, bool):
            # If a bool flag (and is True), the presence of the flag itself is enough.
            continue

        if isinstance(value, list):
            check.list_param(value, f"config.{flag}", of_type=str)
            command_list += value
            continue

        if isinstance(value, dict):
            command_list.append(json.dumps(value))
            continue

        command_list.append(str(value))

    # Execute the dbt CLI command in a subprocess.
    full_command = " ".join(command_list)
    log.info(f"Executing command: {full_command}")

    return_code = 0
    logs = []
    output = []

    process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for raw_line in process.stdout or []:
        line = raw_line.decode("utf-8")
        output.append(line)
        try:
            json_line = json.loads(line)
        except json.JSONDecodeError:
            log.info(line.rstrip())
        else:
            logs.append(json_line)
            level = coerce_valid_log_level(
                json_line.get("levelname", json_line.get("level", "info"))
            )
            log.log(level, json_line.get("message", json_line.get("msg", line.rstrip())))

    process.wait()
    return_code = process.returncode

    log.info("dbt exited with return code {return_code}".format(return_code=return_code))

    raw_output = "\n".join(output)

    if return_code == 2:
        raise DagsterDbtCliFatalRuntimeError(logs=logs, raw_output=raw_output)

    if return_code == 1 and not ignore_handled_error:
        raise DagsterDbtCliHandledRuntimeError(logs=logs, raw_output=raw_output)

    run_results = (
        parse_run_results(flags_dict["project-dir"], target_path)
        if command in DBT_RUN_RESULTS_COMMANDS
        else {}
    )

    return DbtCliOutput(
        command=full_command,
        return_code=return_code,
        raw_output=raw_output,
        logs=logs,
        result=run_results,
        docs_url=docs_url,
    )


def parse_run_results(path: str, target_path: str = DEFAULT_DBT_TARGET_PATH) -> Dict[str, Any]:
    """Parses the `target/run_results.json` artifact that is produced by a dbt process."""
    run_results_path = os.path.join(path, target_path, "run_results.json")
    try:
        with open(run_results_path, encoding="utf8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise DagsterDbtCliOutputsNotFoundError(path=run_results_path)


def parse_manifest(path: str, target_path: str = DEFAULT_DBT_TARGET_PATH) -> Dict[str, Any]:
    """Parses the `target/manifest.json` artifact that is produced by a dbt process."""
    manifest_path = os.path.join(path, target_path, "manifest.json")
    try:
        with open(manifest_path, encoding="utf8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise DagsterDbtCliOutputsNotFoundError(path=manifest_path)
