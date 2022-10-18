import functools
import glob
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

import packaging.version
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
    return subprocess.check_output(["git", "rev-parse", "--short", rev]).decode("utf-8").strip()


@functools.lru_cache(maxsize=None)
def get_changed_files():
    subprocess.call(["git", "fetch", "origin", "master"])
    origin = get_commit("origin/master")
    head = get_commit("HEAD")
    logging.info(f"Changed files between origin/master ({origin}) and HEAD ({head}):")
    paths = (
        subprocess.check_output(["git", "diff", "origin/master...HEAD", "--name-only"])
        .decode("utf-8")
        .strip()
        .split("\n")
    )
    for path in paths:
        logging.info(path)
    return [Path(path) for path in paths]


def skip_if_no_python_changes():
    if not is_feature_branch(os.getenv("BUILDKITE_BRANCH")):
        return None

    if not any(path.suffix == ".py" for path in get_changed_files()):
        return "No python changes"

    return None


@functools.lru_cache(maxsize=None)
def skip_if_no_helm_changes():
    if not is_feature_branch(os.getenv("BUILDKITE_BRANCH")):
        return None

    if any(Path("helm") in path.parents for path in get_changed_files()):
        logging.info("Run helm steps because files in the helm directory changed")
        return None

    return "No helm changes"


@functools.lru_cache(maxsize=None)
def skip_coverage_if_feature_branch():
    if not is_feature_branch(os.getenv("BUILDKITE_BRANCH")):
        return None

    return "Skip coverage uploads until we're finished with our Buildkite refactor"


@functools.lru_cache(maxsize=None)
def python_package_directories():
    # Consider any directory with a setup.py file to be a package
    packages = [Path(setup).parent for setup in glob.glob("**/setup.py", recursive=True)]
    # hidden files are ignored by glob.glob and we don't actually want to recurse
    # all hidden files because there's so much random cruft. So just hardcode the
    # one hidden package we know we need.
    dagster_buildkite = Path(".buildkite/dagster-buildkite")
    packages.append(dagster_buildkite)
    return packages


@functools.lru_cache(maxsize=None)
def changed_python_package_names():
    changes = []

    for directory in python_package_directories():
        for change in get_changed_files():
            if (
                # Our change is in this package's directory
                (change in directory.rglob("*"))
                # The file can alter behavior - exclude things like README changes
                and (change.suffix in [".py", ".cfg", ".toml"])
            ):

                # The file is part of a test suite. We treat these two cases
                # differently because we don't need to run tests in dependent packages
                # if only a test in an upstream package changed.
                if not any(part.endswith("tests") for part in change.parts):
                    changes.append(directory.name)

    return changes
