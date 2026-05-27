import os
import re
import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepConfiguration,
    ResourceRequests,
)
from buildkite_shared.step_builders.slug import slugify_label
from buildkite_shared.tox import build_tox_step as _shared_build_tox_step
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
        pytest_args: Extra arguments passed to pytest via tox posargs. Useful for
            scoping a factor to specific test files, or for excluding test files
            from a residual factor with --ignore=<path>.
        label_suffix: Optional suffix appended to the Buildkite step label, used
            to differentiate multiple factors that share the same factor name.
        queue: Optional Buildkite queue override for this factor. When set,
            takes precedence over the PackageSpec-level queue.
        resources: Optional Kubernetes resource requests for this factor. Only
            takes effect on Kubernetes queues; ignored on EC2 queues.
        soft_fail: If True, this factor's steps don't fail the build when they
            fail. Use for known-flaky suites that are temporarily quarantined.
    """

    factor: str
    splits: int = 1
    concurrency: int | None = None
    concurrency_group: str | None = None
    pytest_args: list[str] | None = None
    label_suffix: str | None = None
    queue: BuildkiteQueue | None = None
    resources: ResourceRequests | None = None
    soft_fail: bool = False


_COMMAND_TYPE_TO_EMOJI_MAP = {
    "pytest": ":pytest:",
    "miscellaneous": ":sparkle:",
}


def build_tox_step(
    root_dir: str | Path,
    tox_env: str,
    base_label: str | None = None,
    command_type: str = "miscellaneous",
    python_version: AvailablePythonVersion | None = None,
    tox_file: str | None = None,
    extra_commands_pre: list[str] | None = None,
    extra_commands_post: list[str] | None = None,
    env: list[str] | None = None,
    depends_on: list[str] | Sequence[str] | None = None,
    timeout_in_minutes: int | None = None,
    queue: BuildkiteQueue | None = None,
    skip_reason: str | None = None,
    pytest_args: list[str] | None = None,
    concurrency: int | None = None,
    concurrency_group: str | None = None,
    resources: ResourceRequests | None = None,
    soft_fail: bool = False,
    ecr_passthru: bool = False,
) -> CommandStepConfiguration:
    base_label = base_label or os.path.basename(root_dir)
    emoji = _COMMAND_TYPE_TO_EMOJI_MAP[command_type]
    key = slugify_label(f"{base_label} {_tox_env_to_label_suffix(tox_env)}")
    resolved_python_version = python_version or _resolve_python_version(tox_env)

    header_message = f"{emoji} Running tox env: {tox_env}"
    section_header = shlex.quote(make_buildkite_section_header(header_message))

    return _shared_build_tox_step(
        root_dir,
        tox_env,
        key=key,
        label_emojis=[emoji],
        timeout_in_minutes=timeout_in_minutes,
        tox_file=tox_file,
        extra_commands_pre=extra_commands_pre,
        extra_commands_post=extra_commands_post,
        env=env,
        # OSS tox suites broadly use docker-compose-backed fixtures (postgres,
        # redis, kafka, redpanda), so opt the whole factory in.
        with_docker=True,
        image="test",
        python_version=resolved_python_version,
        queue=queue,
        depends_on=depends_on,
        skip_reason=skip_reason,
        pytest_args=pytest_args,
        concurrency=concurrency,
        concurrency_group=concurrency_group,
        resources=resources,
        soft_fail=soft_fail,
        ecr_passthru=ecr_passthru,
        section_header=section_header,
    )


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
