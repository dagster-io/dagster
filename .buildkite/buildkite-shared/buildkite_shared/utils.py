import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import yaml


@contextmanager
def pushd(path: Path) -> Iterator[None]:
    prev_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)


def dump_pipeline_yaml(pipeline_dict: dict[str, object]) -> str:
    _assert_step_keys_present_and_unique(pipeline_dict)
    return yaml.dump(pipeline_dict, default_flow_style=False, Dumper=QuotedStrDumper)


def _assert_step_keys_present_and_unique(pipeline_dict: dict[str, object]) -> None:
    """Raise if any step is missing a `key` or if two steps share the same `key`.

    Walks top-level steps and group sub-steps.
    """
    seen: dict[str, str] = {}
    for step in _iter_pipeline_steps(pipeline_dict):
        label = step.get("label") or step.get("group") or step.get("input") or ""
        key = step.get("key")
        if not key:
            raise ValueError(
                f"Step is missing a key (label={label!r}). "
                "Pass a key as the first argument to the StepBuilder constructor."
            )
        if key in seen:
            raise ValueError(
                f"Duplicate step key {key!r} in pipeline. "
                f"First occurrence: {seen[key]!r}; second occurrence: {label!r}. "
                "Each step must have a unique key — pick a distinct one."
            )
        seen[key] = label


def _iter_pipeline_steps(pipeline_dict: dict[str, object]) -> Iterator[dict]:
    raw_steps = pipeline_dict.get("steps", [])
    if not isinstance(raw_steps, list):
        return
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        yield step
        if "steps" in step and isinstance(step["steps"], list):
            for sub in step["steps"]:
                if isinstance(sub, dict):
                    yield sub


class QuotedStrDumper(yaml.Dumper):
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


QuotedStrDumper.add_representer(str, _str_representer)


_OSS_ROOT = Path(__file__).resolve().parents[3]
_IMAGES_ROOT = _OSS_ROOT / "python_modules" / "automation" / "automation" / "docker" / "images"


def get_image_version(image_name: str) -> str:
    """Returns the image timestamp version. All Python versions must use the same timestamp."""
    with open(_IMAGES_ROOT / image_name / "last_updated.yaml", encoding="utf8") as f:
        versions = set(yaml.safe_load(f).values())
        assert len(versions) == 1
        return versions.pop()


BUILDKITE_TEST_IMAGE_VERSION: str = get_image_version("buildkite-test")
RETRYABLE_INFRA_FAILURE_EXIT_CODE = 200


# Wrap a shell command in an in-process retry loop. On persistent failure, exit
# with RETRYABLE_INFRA_FAILURE_EXIT_CODE, which CommandStepBuilder's auto-retry
# config re-runs as a fresh job. Use this for commands that hit infrastructure
# outside our control: package registries, ECR, pip/uv installs, etc.
def with_infra_retry(command: str, *, backoff_seconds: Sequence[int] = (5, 15)) -> str:
    attempts = " || ".join(["_attempt", *(f"(sleep {s} && _attempt)" for s in backoff_seconds)])
    return f"_attempt() {{ {command}; }}; {attempts} || exit {RETRYABLE_INFRA_FAILURE_EXIT_CODE}"


def discover_git_repo_root() -> str:
    # Walk up the directory tree until we find a .git entry.
    # Use Path.exists (not is_dir) because .git is a file in worktrees.
    current_dir = Path(__file__).resolve().parent
    while True:
        if (current_dir / ".git").exists():
            return str(current_dir)
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            raise Exception("Could not find git repository root")
        current_dir = parent_dir


GIT_REPO_ROOT = discover_git_repo_root()
_INTERNAL_OSS_PREFIX = "dagster-oss"
_IS_INTERNAL = (Path(GIT_REPO_ROOT) / _INTERNAL_OSS_PREFIX).is_dir()


def oss_path(path: str) -> Path:
    """Convert an OSS-relative path to a repo-relative path."""
    if _IS_INTERNAL:
        return Path(_INTERNAL_OSS_PREFIX) / path
    return Path(path)
