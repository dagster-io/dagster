import os
import re
import shlex
from dataclasses import dataclass

from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepBuilder,
    CommandStepConfiguration,
)
from buildkite_shared.uv import UV_PIN
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.utils import make_buildkite_section_header


@dataclass
class ToxFactor:
    """Represents a tox environment factor for configuration.

    Args:
        factor: The tox factor name (e.g., "pytest", "integration")
        splits: Number of parallel splits to generate for this factor (default: 1)
        concurrency: Maximum number of jobs to run concurrently in this factor's
            concurrency group (default: None, no limit)
        concurrency_group: Name of the concurrency group for this factor. Required
            if concurrency is set.
    """

    factor: str
    splits: int = 1
    concurrency: int | None = None
    concurrency_group: str | None = None


_COMMAND_TYPE_TO_EMOJI_MAP = {
    "pytest": ":pytest:",
    "miscellaneous": ":sparkle:",
}


def build_tox_step(
    root_dir: str,
    tox_env: str,
    base_label: str | None = None,
    command_type: str = "miscellaneous",
    python_version: AvailablePythonVersion | None = None,
    tox_file: str | None = None,
    extra_commands_pre: list[str] | None = None,
    extra_commands_post: list[str] | None = None,
    env_vars: list[str] | None = None,
    dependencies: list[str] | None = None,
    retries: int | None = None,
    timeout_in_minutes: int | None = None,
    queue: BuildkiteQueue | None = None,
    skip_reason: str | None = None,
    pytest_args: list[str] | None = None,
    concurrency: int | None = None,
    concurrency_group: str | None = None,
) -> CommandStepConfiguration:
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
            f"-c {tox_file} " if tox_file else None,
            "-vv",  # extra-verbose
            "-e",
            tox_env,
            "--" if pytest_args else None,
            " ".join(pytest_args) if pytest_args else None,
        ],
    )
    tox_command = " ".join(tox_command_parts)
    commands = [
        *(extra_commands_pre or []),
        f"cd {root_dir}",
        f'pip install "{UV_PIN}"',
        f"echo -e {shlex.quote(buildkite_section_header)}",
        tox_command,
        *(extra_commands_post or []),
    ]

    step_builder = (
        add_test_image(CommandStepBuilder(label), python_version, env_vars or [])
        .run(*commands)
        .with_timeout(timeout_in_minutes)
        .with_retry(retries)
        .depends_on(dependencies)
        .skip(skip_reason)
    )

    if queue:
        step_builder.on_queue(queue)

    if concurrency is not None or concurrency_group is not None:
        if concurrency is None or concurrency_group is None:
            raise ValueError("Both 'concurrency' and 'concurrency_group' must be set together")
        step_builder.concurrency(concurrency)
        step_builder.concurrency_group(concurrency_group)

    return step_builder.build()


def _tox_env_to_label_suffix(tox_env: str) -> str:
    py_version, _, factor = tox_env.partition("-")
    m = re.match(r"py(\d+)", py_version)
    if m:
        version_number = m[1]
        number_str = f"{version_number[0]}.{version_number[1:]}"
        if factor == "":
            return number_str

        return f"{factor} {number_str}"
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
