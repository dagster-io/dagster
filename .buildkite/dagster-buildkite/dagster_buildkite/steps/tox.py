import os
import re
import shlex
from typing import List, Optional

from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import BuildkiteQueue, CommandStepBuilder
from dagster_buildkite.utils import CommandStep, make_buildkite_section_header

_COMMAND_TYPE_TO_EMOJI_MAP = {
    "pytest": ":pytest:",
    "mypy": ":mypy:",
    "pylint": ":lint-roller:",
    "miscellaneous": ":sparkle",
}


def build_tox_step(
    root_dir: str,
    tox_env: str,
    base_label: Optional[str] = None,
    command_type: str = "miscellaneous",
    python_version: Optional[AvailablePythonVersion] = None,
    tox_file: Optional[str] = None,
    extra_commands_pre: Optional[List[str]] = None,
    extra_commands_post: Optional[List[str]] = None,
    env_vars: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    retries: Optional[int] = None,
    timeout_in_minutes: Optional[int] = None,
    queue: Optional[BuildkiteQueue] = None,
) -> CommandStep:
    base_label = base_label or os.path.basename(root_dir)
    emoji = _COMMAND_TYPE_TO_EMOJI_MAP[command_type]
    label = f"{emoji} {base_label} {_tox_env_to_label_suffix(tox_env)}"
    python_version = python_version or _resolve_python_version(tox_env)

    header_message = f"{emoji} Running tox env: {tox_env}"
    buildkite_section_header = make_buildkite_section_header(header_message)

    tox_command_parts = filter(
        None,
        [
            "tox",
            "-vv",  # extra-verbose
            "-c %s " % tox_file if tox_file else None,
            "-e",
            tox_env,
        ],
    )
    tox_command = " ".join(tox_command_parts)
    commands = [
        *(extra_commands_pre or []),
        f"cd {root_dir}",
        "pip install -U virtualenv",
        f"echo -e {shlex.quote(buildkite_section_header)}",
        tox_command,
        *(extra_commands_post or []),
    ]

    return (
        CommandStepBuilder(label)
        .run(*commands)
        .with_timeout(timeout_in_minutes)
        .with_retry(retries)
        .with_dependencies(dependencies)
        .with_queue(queue)
        .on_test_image(python_version, env_vars or [])
    ).build()


def _tox_env_to_label_suffix(tox_env: str) -> str:
    py_version, _, factor = tox_env.partition("-")
    m = re.match(r"py(\d+)", py_version)
    if m:
        version_number = m[1]
        number_str = f"{version_number[0]}.{version_number[1:]}"
        return f" {factor} {number_str}"
    else:
        return ""


def _resolve_python_version(tox_env: str) -> AvailablePythonVersion:
    factors = tox_env.split("-")
    py_version_factor = next((f for f in factors if re.match(r"py\d+", f)), None)
    if py_version_factor:
        major, minor = int(py_version_factor[2]), int(py_version_factor[3:])
        return AvailablePythonVersion.from_major_minor(major, minor)
    else:
        return AvailablePythonVersion.get_default()
