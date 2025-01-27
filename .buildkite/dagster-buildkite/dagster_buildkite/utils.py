import functools
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import packaging.version
import yaml
from typing_extensions import Literal, TypeAlias, TypedDict, TypeGuard

from dagster_buildkite.git import ChangedFiles, get_commit_message

BUILD_CREATOR_EMAIL_TO_SLACK_CHANNEL_MAP = {
    "rex@dagsterlabs.com": "eng-buildkite-rex",
    "dish@dagsterlabs.com": "eng-buildkite-dish",
    "johann@dagsterlabs.com": "eng-buildkite-johann",
}

# ########################
# ##### BUILDKITE STEP DATA STRUCTURES
# ########################

# Buildkite step configurations can be quite complex-- the full specifications are in the Pipelines
# -> Step Types section of the Buildkite docs:
#   https://buildkite.com/docs/pipelines/command-step
#
# The structures defined below are subsets of the full specifications that only cover the attributes
# we use. Additional keys can be added from the full spec as needed.


class CommandStep(TypedDict, total=False):
    agents: Dict[str, str]
    commands: List[str]
    depends_on: List[str]
    key: str
    label: str
    plugins: List[Dict[str, object]]
    retry: Dict[str, object]
    timeout_in_minutes: int
    skip: str


class GroupStep(TypedDict):
    group: str
    key: str
    steps: List["BuildkiteLeafStep"]  # no nested groups


# use alt syntax because of `async` and `if` reserved words
TriggerStep = TypedDict(
    "TriggerStep",
    {
        "trigger": str,
        "label": str,
        "async": Optional[bool],
        "build": Dict[str, object],
        "branches": Optional[str],
        "if": Optional[str],
    },
    total=False,
)

WaitStep: TypeAlias = Literal["wait"]

InputSelectOption = TypedDict("InputSelectOption", {"label": str, "value": str})
InputSelectField = TypedDict(
    "InputSelectField",
    {
        "select": str,
        "key": str,
        "options": List[InputSelectOption],
        "hint": Optional[str],
        "default": Optional[str],
        "required": Optional[bool],
        "multiple": Optional[bool],
    },
)
InputTextField = TypedDict(
    "InputTextField",
    {
        "text": str,
        "key": str,
        "hint": Optional[str],
        "default": Optional[str],
        "required": Optional[bool],
    },
)

BlockStep = TypedDict(
    "BlockStep",
    {
        "block": str,
        "prompt": Optional[str],
        "fields": List[Union[InputSelectField, InputTextField]],
    },
)

BuildkiteStep: TypeAlias = Union[
    CommandStep, GroupStep, TriggerStep, WaitStep, BlockStep
]
BuildkiteLeafStep = Union[CommandStep, TriggerStep, WaitStep]
BuildkiteTopLevelStep = Union[CommandStep, GroupStep]

UV_PIN = "uv==0.4.30"


def is_command_step(step: BuildkiteStep) -> TypeGuard[CommandStep]:
    return isinstance(step, dict) and "commands" in step


# ########################
# ##### FUNCTIONS
# ########################


def safe_getenv(env_var: str) -> str:
    assert env_var in os.environ, f"${env_var} must be set."
    return os.environ[env_var]


def buildkite_yaml_for_steps(
    steps: Sequence[BuildkiteStep], custom_slack_channel: Optional[str] = None
) -> str:
    return yaml.dump(
        {
            "env": {
                "CI_NAME": "buildkite",
                "CI_BUILD_NUMBER": "$BUILDKITE_BUILD_NUMBER",
                "CI_BUILD_URL": "$BUILDKITE_BUILD_URL",
                "CI_BRANCH": "$BUILDKITE_BRANCH",
                "CI_PULL_REQUEST": "$BUILDKITE_PULL_REQUEST",
            },
            "steps": steps,
            "notify": [
                {
                    "slack": f"elementl#{slack_channel}",
                    "if": (
                        f"build.creator.email == '{buildkite_email}'  && build.state != 'canceled'"
                    ),
                }
                for buildkite_email, slack_channel in BUILD_CREATOR_EMAIL_TO_SLACK_CHANNEL_MAP.items()
            ]
            + (
                [
                    {
                        "slack": f"elementl#{custom_slack_channel}",
                        "if": "build.state != 'canceled'",
                    }
                ]
                if custom_slack_channel
                else []
            ),
        },
        default_flow_style=False,
    )


def check_for_release() -> bool:
    try:
        git_tag = str(
            subprocess.check_output(
                ["git", "describe", "--exact-match", "--abbrev=0"],
                stderr=subprocess.STDOUT,
            )
        ).strip("'b\\n")
    except subprocess.CalledProcessError:
        return False

    version: Dict[str, object] = {}
    with open("python_modules/dagster/dagster/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    if git_tag == version["__version__"]:
        return True

    return False


def network_buildkite_container(network_name: str) -> List[str]:
    return [
        # hold onto your hats, this is docker networking at its best. First, we figure out
        # the name of the currently running container...
        "export CONTAINER_ID=`cat /etc/hostname`",
        r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
        # then, we dynamically bind this container into the user-defined bridge
        # network to make the target containers visible...
        f"docker network connect {network_name} \\${{CONTAINER_NAME}}",
    ]


def connect_sibling_docker_container(
    network_name: str, container_name: str, env_variable: str
) -> List[str]:
    return [
        # Now, we grab the IP address of the target container from within the target
        # bridge network and export it; this will let the tox tests talk to the target cot.
        f"export {env_variable}=`docker inspect --format "
        f"'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
        f"{container_name}`"
    ]


def is_feature_branch(branch_name: str = safe_getenv("BUILDKITE_BRANCH")) -> bool:
    return not (branch_name == "master" or branch_name.startswith("release"))


def is_release_branch(branch_name: str) -> bool:
    return branch_name.startswith("release-")


# Preceding a line of BK output with "---" turns it into a section header.
# The characters surrounding the `message` are ANSI escope sequences used to colorize the output.
# Note that "\" is doubled below to insert a single literal backslash in the string.
#
# \033[0;32m : initiate green coloring
# \033[0m : end coloring
#
# Green is hardcoded, but can easily be parameterized if needed.
def make_buildkite_section_header(message: str) -> str:
    return f"--- \\033[0;32m{message}\\033[0m"


# Use this to get the "library version" (pre-1.0 version) from the "core version" (post 1.0
# version). 16 is from the 0.16.0 that library versions stayed on when core went to 1.0.0.
def library_version_from_core_version(core_version: str) -> str:
    release = parse_package_version(core_version).release
    if release[0] >= 1:
        return ".".join(["0", str(16 + release[1]), str(release[2])])
    else:
        return core_version


def parse_package_version(version_str: str) -> packaging.version.Version:
    parsed_version = packaging.version.parse(version_str)
    assert isinstance(
        parsed_version, packaging.version.Version
    ), f"Found LegacyVersion: {version_str}"
    return parsed_version


def get_commit(rev):
    return (
        subprocess.check_output(["git", "rev-parse", "--short", rev])
        .decode("utf-8")
        .strip()
    )


def skip_if_no_python_changes(overrides: Optional[Sequence[str]] = None):
    if message_contains("NO_SKIP"):
        return None

    if not is_feature_branch():
        return None

    if any(path.suffix == ".py" for path in ChangedFiles.all):
        return None

    if overrides and any(
        Path(override) in path.parents
        for override in overrides
        for path in ChangedFiles.all
    ):
        return None

    return "No python changes"


def skip_if_no_pyright_requirements_txt_changes():
    if message_contains("NO_SKIP"):
        return None

    if not is_feature_branch():
        return None

    if any(path.match("pyright/*/requirements.txt") for path in ChangedFiles.all):
        return None

    return "No pyright requirements.txt changes"


def skip_if_no_yaml_changes():
    if message_contains("NO_SKIP"):
        return None

    if not is_feature_branch():
        return None

    if any(path.suffix in [".yml", ".yaml"] for path in ChangedFiles.all):
        return None

    return "No yaml changes"


def skip_if_no_non_docs_markdown_changes():
    if message_contains("NO_SKIP"):
        return None

    if not is_feature_branch():
        return None

    if any(
        path.suffix == ".md" and Path("docs") not in path.parents
        for path in ChangedFiles.all
    ):
        return None

    return "No markdown changes outside of docs"


@functools.lru_cache(maxsize=None)
def has_helm_changes():
    return any(Path("helm") in path.parents for path in ChangedFiles.all)


@functools.lru_cache(maxsize=None)
def has_dagster_airlift_changes():
    return any("dagster-airlift" in str(path) for path in ChangedFiles.all)


@functools.lru_cache(maxsize=None)
def skip_if_not_airlift_or_dlift_commit() -> Optional[str]:
    """If no dlift or airlift files are touched, then do NOT run. Even if on master."""
    return (
        None
        if (
            any("dagster-dlift" in str(path) for path in ChangedFiles.all)
            or any("dagster-airlift" in str(path) for path in ChangedFiles.all)
        )
        else "Not an airlift or dlift commit"
    )


@functools.lru_cache(maxsize=None)
def has_storage_test_fixture_changes():
    # Attempt to ensure that changes to TestRunStorage and TestEventLogStorage suites trigger integration
    return any(
        Path("python_modules/dagster/dagster_tests/storage_tests/utils") in path.parents
        for path in ChangedFiles.all
    )


def skip_if_not_dlift_commit() -> Optional[str]:
    """If no dlift files are touched, then do NOT run. Even if on master."""
    return (
        None
        if any("dagster-dlift" in str(path) for path in ChangedFiles.all)
        else "Not a dlift commit"
    )


def skip_if_no_helm_changes():
    if message_contains("NO_SKIP"):
        return None

    if not is_feature_branch():
        return None

    if has_helm_changes():
        logging.info("Run helm steps because files in the helm directory changed")
        return None

    return "No helm changes"


def message_contains(substring: str) -> bool:
    return any(
        substring in message
        for message in [os.getenv("BUILDKITE_MESSAGE", ""), get_commit_message("HEAD")]
    )


def skip_if_no_docs_changes():
    if message_contains("NO_SKIP"):
        return None

    if not is_feature_branch(os.getenv("BUILDKITE_BRANCH")):  # pyright: ignore[reportArgumentType]
        return None

    # If anything changes in the docs directory
    if any(Path("docs") in path.parents for path in ChangedFiles.all):
        logging.info("Run docs steps because files in the docs directory changed")
        return None

    # If anything changes in the examples directory. This is where our docs snippets live.
    if any(Path("examples") in path.parents for path in ChangedFiles.all):
        logging.info("Run docs steps because files in the examples directory changed")
        return None

    return "No docs changes"
