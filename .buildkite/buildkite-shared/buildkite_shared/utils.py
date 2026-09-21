import logging
import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import yaml
from dagster_shared.yaml_utils import safe_load_yaml


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
    pipeline_dict = _drop_skipped_steps(pipeline_dict)
    return yaml.dump(pipeline_dict, default_flow_style=False, Dumper=QuotedStrDumper)


def _drop_skipped_steps(pipeline_dict: dict[str, object]) -> dict[str, object]:
    """Remove any step with a truthy ``skip`` field from the pipeline.

    Skipped steps still show up in the Buildkite UI / API as "broken" jobs even
    though they never run; uploading them just makes the build noisier. We log
    each drop to stderr so the reason is preserved.

    Also drops ``depends_on`` references that point at dropped step keys, and
    drops any group whose substeps were all skipped.
    """
    raw_steps = pipeline_dict.get("steps")
    if not isinstance(raw_steps, list):
        return pipeline_dict

    dropped_keys: set[str] = set()

    def _is_skipped(step: object) -> bool:
        return isinstance(step, dict) and bool(step.get("skip"))

    def _describe(step: dict) -> str:
        return step.get("key") or step.get("label") or step.get("group") or "<unknown>"

    kept_steps: list[object] = []
    for step in raw_steps:
        if not isinstance(step, dict):
            kept_steps.append(step)
            continue

        if _is_skipped(step):
            logging.info("Dropping skipped step %s: %s", _describe(step), step["skip"])
            key = step.get("key")
            if key:
                dropped_keys.add(key)
            continue

        kept = step
        substeps = step.get("steps")
        if isinstance(substeps, list):
            new_substeps = []
            for sub in substeps:
                if _is_skipped(sub):
                    assert isinstance(sub, dict)
                    logging.info("Dropping skipped step %s: %s", _describe(sub), sub["skip"])
                    sub_key = sub.get("key")
                    if sub_key:
                        dropped_keys.add(sub_key)
                else:
                    new_substeps.append(sub)
            if not new_substeps:
                logging.info(
                    "Dropping empty group %s (all substeps were skipped)",
                    _describe(step),
                )
                group_key = step.get("key")
                if group_key:
                    dropped_keys.add(group_key)
                continue
            kept = {**step, "steps": new_substeps}

        kept_steps.append(kept)

    if dropped_keys:
        kept_steps = [_scrub_depends_on(s, dropped_keys) for s in kept_steps]

    return {**pipeline_dict, "steps": kept_steps}


def _scrub_depends_on(step: object, dropped_keys: set[str]) -> object:
    """Remove dropped-step keys from a step's ``depends_on`` list, recursing into groups."""
    if not isinstance(step, dict):
        return step
    new_step = step
    deps = step.get("depends_on")
    if isinstance(deps, list):
        filtered = [d for d in deps if d not in dropped_keys]
        if filtered != deps:
            new_step = {**new_step, "depends_on": filtered}
    substeps = new_step.get("steps")
    if isinstance(substeps, list):
        new_step = {
            **new_step,
            "steps": [_scrub_depends_on(s, dropped_keys) for s in substeps],
        }
    return new_step


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
        versions = set(safe_load_yaml(f).values())
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


def network_buildkite_container(network_name: str) -> list[str]:
    return [
        # Set Docker API version for compatibility with older daemons
        "export DOCKER_API_VERSION=1.41",
        # hold onto your hats, this is docker networking at its best. First, we figure out
        # the name of the currently running container...
        "export CONTAINER_ID=`cat /etc/hostname`",
        r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
        # then, we dynamically bind this container into the user-defined bridge
        # network to make the target containers visible. On Kubernetes the
        # job runs in a pod (not a docker container), so CONTAINER_NAME is
        # empty; the DinD sidecar shares the pod's network namespace, so the
        # bridge is already reachable and we skip the connect step.
        rf'if [ -n "\${{CONTAINER_NAME}}" ]; then docker network connect {network_name} \${{CONTAINER_NAME}}; fi',
    ]


def connect_sibling_docker_container(
    network_name: str, container_name: str, env_variable: str
) -> list[str]:
    return [
        # Now, we grab the IP address of the target container from within the target
        # bridge network and export it; this will let the tox tests talk to the target cot.
        f"export {env_variable}=`docker inspect --format "
        f"'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
        f"{container_name}`"
    ]


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
