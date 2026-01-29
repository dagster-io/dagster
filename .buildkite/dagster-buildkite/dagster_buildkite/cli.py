import logging
import os
from pathlib import Path

# Configure logging based on LOGLEVEL env var (default to WARNING)
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOGLEVEL", "WARNING").upper(), logging.WARNING),
    format="%(levelname)s: %(message)s",
)

from buildkite_shared.git import GitInfo
from buildkite_shared.python_packages import PythonPackages
from dagster_buildkite.pipelines.dagster_oss_main import build_dagster_oss_main_steps
from dagster_buildkite.pipelines.dagster_oss_nightly_pipeline import build_dagster_oss_nightly_steps
from dagster_buildkite.pipelines.prerelease_package import build_prerelease_package_steps
from dagster_buildkite.utils import buildkite_yaml_for_steps

CLI_HELP = """This CLI is used for generating Buildkite YAML. Each function corresponds to an entry
point defined in `setup.py`. Buildkite invokes these entry points when loading the specification for
a pipeline.
"""


def _running_from_internal_repo() -> bool:
    """Check if we're running from the internal repo root (not standalone OSS repo).

    We check for dagster-oss/ directory existing, which indicates we're at internal root.
    (Can't check dagster-cloud/ because oss-tests pipeline may use sparse checkout.)
    """
    result = Path("dagster-oss").is_dir()
    logging.info(f"_running_from_internal_repo: cwd={os.getcwd()}, dagster-oss exists={result}")
    return result


def _ensure_oss_root() -> bool:
    """Change to OSS repo root if running from internal. Returns True if we're on internal."""
    if _running_from_internal_repo():
        os.chdir("dagster-oss")
        logging.info(f"_ensure_oss_root: changed to {os.getcwd()}")
        return True
    logging.info(f"_ensure_oss_root: staying in {os.getcwd()}")
    return False


def _prefix_commands_with_cd(steps: list) -> None:
    """Prefix all commands with 'cd dagster-oss' for running OSS steps from internal repo."""
    for step in steps:
        if "commands" in step:
            step["commands"] = ["cd dagster-oss", *step["commands"]]
        # Handle grouped steps
        if "steps" in step:
            _prefix_commands_with_cd(step["steps"])


def dagster() -> None:
    is_internal = _ensure_oss_root()
    PythonPackages.load_from_git(GitInfo(directory=Path(".")))
    steps = build_dagster_oss_main_steps()
    if is_internal:
        _prefix_commands_with_cd(steps)
    buildkite_yaml = buildkite_yaml_for_steps(steps)
    print(buildkite_yaml)  # noqa: T201


def dagster_nightly() -> None:
    is_internal = _ensure_oss_root()
    PythonPackages.load_from_git(GitInfo(directory=Path(".")))
    steps = build_dagster_oss_nightly_steps()
    if is_internal:
        _prefix_commands_with_cd(steps)
    buildkite_yaml = buildkite_yaml_for_steps(steps, custom_slack_channel="eng-buildkite-nightly")
    print(buildkite_yaml)  # noqa: T201


def prerelease_package() -> None:
    is_internal = _ensure_oss_root()
    PythonPackages.load_from_git(GitInfo(directory=Path(".")))
    steps = build_prerelease_package_steps()
    if is_internal:
        _prefix_commands_with_cd(steps)
    buildkite_yaml = buildkite_yaml_for_steps(steps)
    print(buildkite_yaml)  # noqa: T201
