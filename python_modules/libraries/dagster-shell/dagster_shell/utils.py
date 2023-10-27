#
# NOTE: This file is based on the bash operator from Apache Airflow, which can be found here:
# https://github.com/apache/airflow/blob/master/airflow/operators/bash.py
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os
import signal
from logging import Logger
from subprocess import PIPE, STDOUT, Popen
from typing import Mapping, Optional, Tuple

import dagster._check as check
from dagster._utils import safe_tempfile_path
from typing_extensions import Final

OUTPUT_LOGGING_OPTIONS: Final = ["STREAM", "BUFFER", "NONE"]


def execute_script_file(
    shell_script_path: str,
    output_logging: str,
    log: Logger,
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[str, int]:
    """Execute a shell script file specified by the argument ``shell_script_path``. The script will be
    invoked via ``subprocess.Popen(['bash', shell_script_path], ...)``.

    In the Popen invocation, ``stdout=PIPE, stderr=STDOUT`` is used, and the combined stdout/stderr
    output is retrieved.

    Examples:
        .. literalinclude:: ../../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_script_utility.py
           :language: python

    Args:
        shell_script_path (str): The shell script to execute.
        output_logging (str): The logging mode to use. Supports STREAM, BUFFER, and NONE.
        log (Union[logging.Logger, DagsterLogManager]): Any logger which responds to .info()
        cwd (str, optional): Working directory for the shell command to use. Defaults to the
            temporary path where we store the shell command in a script file.
        env (Dict[str, str], optional): Environment dictionary to pass to ``subprocess.Popen``.
            Unused by default.

    Raises:
        Exception: When an invalid output_logging is selected. Unreachable from op-based
            invocation since the config system will check output_logging against the config
            enum.

    Returns:
        Tuple[str, int]: A tuple where the first element is the combined stdout/stderr output of running the shell
        command and the second element is the return code.
    """
    check.str_param(shell_script_path, "shell_script_path")
    check.str_param(output_logging, "output_logging")
    check.opt_str_param(cwd, "cwd", default=os.path.dirname(shell_script_path))
    env = check.opt_nullable_dict_param(env, "env", key_type=str, value_type=str)

    if output_logging not in OUTPUT_LOGGING_OPTIONS:
        raise Exception("Unrecognized output_logging %s" % output_logging)

    def pre_exec():
        # Restore default signal disposition and invoke setsid
        for sig in ("SIGPIPE", "SIGXFZ", "SIGXFSZ"):
            if hasattr(signal, sig):
                signal.signal(getattr(signal, sig), signal.SIG_DFL)
        os.setsid()

    with open(shell_script_path, "rb") as f:
        shell_command = f.read().decode("utf-8")

    log.info(f"Running command:\n{shell_command}")

    sub_process = None
    try:
        stdout_pipe = PIPE
        stderr_pipe = STDOUT
        if output_logging == "NONE":
            stdout_pipe = stderr_pipe = None

        sub_process = Popen(
            ["bash", shell_script_path],
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            cwd=cwd,
            env=env,
            preexec_fn=pre_exec,  # noqa: PLW1509
            encoding="UTF-8",
        )

        log.info(f"Command pid: {sub_process.pid}")

        output = ""
        if output_logging == "STREAM":
            assert sub_process.stdout is not None, "Setting stdout=PIPE should always set stdout."
            # Stream back logs as they are emitted
            lines = []
            for line in sub_process.stdout:
                log.info(line.rstrip())
                lines.append(line)
            output = "".join(lines)
        elif output_logging == "BUFFER":
            # Collect and buffer all logs, then emit
            output, _ = sub_process.communicate()
            log.info(output)

        sub_process.wait()
        log.info(f"Command exited with return code {sub_process.returncode}")

        return output, sub_process.returncode
    finally:
        # Always terminate subprocess, including in cases where the run is terminated
        if sub_process:
            sub_process.terminate()


def execute(
    shell_command: str,
    output_logging: str,
    log: Logger,
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[str, int]:
    """This function is a utility for executing shell commands from within a Dagster op (or from Python in general).
    It can be used to execute shell commands on either op input data, or any data generated within a generic python op.

    Internally, it executes a shell script specified by the argument ``shell_command``. The script will be written
    to a temporary file first and invoked via ``subprocess.Popen(['bash', shell_script_path], ...)``.

    In the Popen invocation, ``stdout=PIPE, stderr=STDOUT`` is used, and the combined stdout/stderr
    output is retrieved.

    Examples:
        .. literalinclude:: ../../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_command_utility.py
           :language: python

    Args:
        shell_command (str): The shell command to execute
        output_logging (str): The logging mode to use. Supports STREAM, BUFFER, and NONE.
        log (Union[logging.Logger, DagsterLogManager]): Any logger which responds to .info()
        cwd (str, optional): Working directory for the shell command to use. Defaults to the
            temporary path where we store the shell command in a script file.
        env (Dict[str, str], optional): Environment dictionary to pass to ``subprocess.Popen``.
            Unused by default.

    Returns:
        Tuple[str, int]: A tuple where the first element is the combined stdout/stderr output of running the shell
        command and the second element is the return code.
    """
    check.str_param(shell_command, "shell_command")
    # other args checked in execute_file

    with safe_tempfile_path() as tmp_file_path:
        tmp_path = os.path.dirname(tmp_file_path)
        log.info("Using temporary directory: %s" % tmp_path)

        with open(tmp_file_path, "wb") as tmp_file:
            tmp_file.write(shell_command.encode("utf-8"))
            tmp_file.flush()
            script_location = os.path.abspath(tmp_file.name)
            log.info(f"Temporary script location: {script_location}")
            return execute_script_file(
                shell_script_path=tmp_file.name,
                output_logging=output_logging,
                log=log,
                cwd=(cwd or tmp_path),
                env=env,
            )
