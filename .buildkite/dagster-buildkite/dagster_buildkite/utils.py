import os
import subprocess

import yaml

from .defines import SupportedPython, SupportedPythons

DAGIT_PATH = "js_modules/dagit"


def buildkite_yaml_for_steps(steps):
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
        },
        default_flow_style=False,
    )


def check_for_release():
    try:
        git_tag = str(
            subprocess.check_output(
                ["git", "describe", "--exact-match", "--abbrev=0"], stderr=subprocess.STDOUT
            )
        ).strip("'b\\n")
    except subprocess.CalledProcessError:
        return False

    version = {}
    with open("python_modules/dagster/dagster/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if git_tag == version["__version__"]:
        return True

    return False


def is_pr_and_dagit_only():
    branch_name = os.getenv("BUILDKITE_BRANCH")
    base_branch = os.getenv("BUILDKITE_PULL_REQUEST_BASE_BRANCH")

    if branch_name is None or branch_name == "master" or branch_name.startswith("release"):
        return False

    try:
        pr_commit = os.getenv("BUILDKITE_COMMIT")
        origin_base = "origin/" + base_branch
        diff_files = (
            subprocess.check_output(["git", "diff", origin_base, pr_commit, "--name-only"])
            .decode("utf-8")
            .strip()
            .split("\n")
        )
        return all(filepath.startswith(DAGIT_PATH) for (filepath) in diff_files)

    except subprocess.CalledProcessError:
        return False


def network_buildkite_container(network_name):
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


def connect_sibling_docker_container(network_name, container_name, env_variable):
    return [
        # Now, we grab the IP address of the target container from within the target
        # bridge network and export it; this will let the tox tests talk to the target cot.
        (
            "export {env_variable}=`docker inspect --format "
            "'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
            "{container_name}`".format(
                network_name=network_name, container_name=container_name, env_variable=env_variable
            )
        )
    ]


def is_release_branch(branch_name: str):
    return branch_name.startswith("release-")


# To test the full suite of Python versions on a PR, include this string anywhere in the branch name
# or commit message.
FULL_BUILD_MARKER_STR = "fullbuild"

# To more specifically customize the tested Python versions for a branch, set environment variable
# $DEFAULT_PYTHON_VERSIONS to a comma-separated list of python version specifiers of the form VX_Y
# (i.e. attributes of `SupportedPython`).
_versions = os.environ.get("DEFAULT_PYTHON_VERSIONS", "V3_9")
DEFAULT_PYTHON_VERSIONS = [getattr(SupportedPython, ver) for ver in _versions.split(",")]

# By default only one representative Python version is tested on PRs, and all versions are
# tested on master or release branches.
def get_python_versions_for_branch(pr_versions=None):
    pr_versions = pr_versions if pr_versions != None else DEFAULT_PYTHON_VERSIONS

    branch_name = os.getenv("BUILDKITE_BRANCH")
    assert branch_name is not None, "$BUILDKITE_BRANCH env var must be set."
    commit_message = os.getenv("BUILDKITE_MESSAGE")
    assert commit_message is not None, "$BUILDKITE_MESSAGE env var must be set."

    if (
        branch_name == "master"
        or is_release_branch(branch_name)
        or FULL_BUILD_MARKER_STR in branch_name
        or FULL_BUILD_MARKER_STR in commit_message
    ):
        return SupportedPythons
    else:
        return pr_versions
