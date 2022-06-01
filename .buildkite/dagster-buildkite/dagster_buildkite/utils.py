import os
import subprocess
from typing import Dict, List, Optional, Union

import yaml
from typing_extensions import Literal, TypeAlias, TypedDict

BUILD_CREATOR_EMAIL_TO_SLACK_CHANNEL_MAP = {
    "rex@elementl.com": "eng-buildkite-rex",
    "dish@elementl.com": "eng-buildkite-dish",
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

BuildkiteStep: TypeAlias = Union[CommandStep, GroupStep, TriggerStep, WaitStep]
BuildkiteLeafStep = Union[CommandStep, TriggerStep, WaitStep]

# ########################
# ##### FUNCTIONS
# ########################


def safe_getenv(env_var: str) -> str:
    assert env_var in os.environ, f"${env_var} must be set."
    return os.environ[env_var]


def buildkite_yaml_for_steps(steps) -> str:
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
                    "if": f"build.creator.email == '{buildkite_email}'  && build.state != 'canceled'",
                }
                for buildkite_email, slack_channel in BUILD_CREATOR_EMAIL_TO_SLACK_CHANNEL_MAP.items()
            ],
        },
        default_flow_style=False,
    )


def check_for_release() -> bool:
    try:
        git_tag = str(
            subprocess.check_output(
                ["git", "describe", "--exact-match", "--abbrev=0"], stderr=subprocess.STDOUT
            )
        ).strip("'b\\n")
    except subprocess.CalledProcessError:
        return False

    version: Dict[str, object] = {}
    with open("python_modules/dagster/dagster/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if git_tag == version["__version__"]:
        return True

    return False


def network_buildkite_container(network_name: str) -> List[str]:
    return [
        # hold onto your hats, this is docker networking at its best. First, we figure out
        # the name of the currently running container...
        "export CONTAINER_ID=`cut -c9- < /proc/1/cpuset`",
        r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
        # then, we dynamically bind this container into the user-defined bridge
        # network to make the target containers visible...
        "docker network connect {network_name} \\${{CONTAINER_NAME}}".format(
            network_name=network_name
        ),
    ]


def connect_sibling_docker_container(
    network_name: str, container_name: str, env_variable: str
) -> List[str]:
    return [
        # Now, we grab the IP address of the target container from within the target
        # bridge network and export it; this will let the tox tests talk to the target cot.
        (
            f"export {env_variable}=`docker inspect --format "
            f"'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
            f"{container_name}`"
        )
    ]


def is_feature_branch(branch_name: str) -> bool:
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
