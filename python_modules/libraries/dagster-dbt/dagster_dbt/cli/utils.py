import json
import os
import re
import signal
import subprocess
from typing import List, Tuple

from dagster import check

from ..errors import DagsterDbtFatalCliRuntimeError, DagsterDbtHandledCliRuntimeError


def pre_exec():
    # Restore default signal disposition and invoke setsid
    for sig in ("SIGPIPE", "SIGXFZ", "SIGXFSZ"):
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), signal.SIG_DFL)
    os.setsid()


def execute_dbt(
    executable, command, flags_dict, log, warn_error, ignore_handled_error
) -> Tuple[List[dict], str, int]:
    check.tuple_param(command, "command", of_type=str)
    check.dict_param(flags_dict, "flags_dict", key_type=str)
    check.bool_param(warn_error, "warn_error")
    check.bool_param(ignore_handled_error, "ignore_handled_error")

    warn_error = ["--warn-error"] if warn_error else []
    command_list = [executable, "--log-format", "json", *warn_error, *command]
    for flag, value in flags_dict.items():
        if not value:
            continue
        command_list.append(f"--{flag}")

        if isinstance(value, bool):  # if a bool flag (and is True), the flag itself is enough
            continue
        elif isinstance(value, list):
            check.list_param(value, f"config.{flag}", of_type=str)
            command_list += value
        elif isinstance(value, dict):
            command_list.append(json.dumps(value))
        else:
            command_list.append(str(value))

    log.info(f"Executing command: $ {' '.join(command_list)}")

    return_code = 0
    try:
        proc_out = subprocess.check_output(
            command_list, preexec_fn=pre_exec, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as exc:
        return_code = exc.returncode
        proc_out = exc.output

    parsed_output = []
    for raw_line in proc_out.strip().split(b"\n"):
        line = raw_line.decode()
        log.info(line.rstrip())
        try:
            json_line = json.loads(line)
            parsed_output.append(json_line)
        except json.JSONDecodeError:
            pass

    log.info("dbt exited with return code {retcode}".format(retcode=return_code))

    if return_code == 2:
        raise DagsterDbtFatalCliRuntimeError(
            parsed_output=parsed_output, raw_output=proc_out.decode()
        )

    if return_code == 1 and not ignore_handled_error:
        raise DagsterDbtHandledCliRuntimeError(
            parsed_output=parsed_output, raw_output=proc_out.decode()
        )

    return parsed_output, proc_out.decode(), return_code


RESULT_STATS_RE = re.compile(r"PASS=(\d+) WARN=(\d+) ERROR=(\d+) SKIP=(\d+) TOTAL=(\d+)")
RESULT_STATS_LABELS = ("n_pass", "n_warn", "n_error", "n_skip", "n_total")


def get_run_results(parsed_output):
    check.list_param(parsed_output, "parsed_output", dict)

    last_line = parsed_output[-1]
    message = last_line["message"].strip()

    try:
        matches = next(RESULT_STATS_RE.finditer(message)).groups()
    except StopIteration:
        matches = [None] * 5  # anticipating a regex problem

    return dict(zip(RESULT_STATS_LABELS, matches))
