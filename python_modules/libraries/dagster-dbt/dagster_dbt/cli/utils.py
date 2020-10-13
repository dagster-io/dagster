import json
import os
import re
import subprocess
from typing import Any, Dict, List, Tuple

from dagster import check

from ..errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
)


def execute_cli(
    executable: str,
    command: Tuple[str, ...],
    flags_dict: Dict[str, Any],
    log: Any,
    warn_error: bool,
    ignore_handled_error: bool,
) -> Dict[str, Any]:
    """Executes a command on the dbt CLI in a subprocess."""
    check.str_param(executable, "executable")
    check.tuple_param(command, "command", of_type=str)
    check.dict_param(flags_dict, "flags_dict", key_type=str)
    check.bool_param(warn_error, "warn_error")
    check.bool_param(ignore_handled_error, "ignore_handled_error")

    # Format the dbt CLI flags in the command..
    warn_error = ["--warn-error"] if warn_error else []
    command_list = [executable, "--log-format", "json", *warn_error, *command]

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
    command = " ".join(command_list)
    log.info(f"Executing command: $ {command}")

    return_code = 0
    try:
        proc_out = subprocess.check_output(args=command_list, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        return_code = exc.returncode
        proc_out = exc.output

    # Parse the JSON logs from the dbt process.
    logs = []
    for raw_line in proc_out.strip().split(b"\n"):
        line = raw_line.decode()
        log.info(line.rstrip())
        try:
            json_line = json.loads(line)
        except json.JSONDecodeError:
            pass
        else:
            logs.append(json_line)

    log.info("dbt exited with return code {return_code}".format(return_code=return_code))

    if return_code == 2:
        raise DagsterDbtCliFatalRuntimeError(logs=logs, raw_output=proc_out.decode())

    if return_code == 1 and not ignore_handled_error:
        raise DagsterDbtCliHandledRuntimeError(logs=logs, raw_output=proc_out.decode())

    return {
        "command": command,
        "return_code": return_code,
        "logs": logs,
        "raw_output": proc_out.decode(),
        "summary": extract_summary(logs),
    }


SUMMARY_RE = re.compile(r"PASS=(\d+) WARN=(\d+) ERROR=(\d+) SKIP=(\d+) TOTAL=(\d+)")
SUMMARY_LABELS = ("num_pass", "num_warn", "num_error", "num_skip", "num_total")


def extract_summary(logs: List[Dict[str, str]]):
    """Extracts the summary statistics from dbt CLI output."""
    check.list_param(logs, "logs", dict)

    summary = [None] * 5

    if len(logs) > 0:
        # Attempt to extract summary results from the last log's message.
        last_line = logs[-1]
        message = last_line["message"].strip()

        try:
            summary = next(SUMMARY_RE.finditer(message)).groups()
        except StopIteration:
            # Failed to match regex.
            pass
        else:
            summary = map(int, summary)

    return dict(zip(SUMMARY_LABELS, summary))


def parse_run_results(path: str) -> Dict[str, Any]:
    """Parses the `target/run_results.json` artifact that is produced by a dbt process."""
    run_results_path = os.path.join(path, "target", "run_results.json")
    try:
        with open(run_results_path) as file:
            return json.load(file)
    except FileNotFoundError:
        raise DagsterDbtCliOutputsNotFoundError(path=run_results_path)
