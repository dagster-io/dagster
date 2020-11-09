import os
import subprocess

DAGIT_PATH = "js_modules/dagit"


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
    with open("python_modules/dagster/dagster/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    if git_tag == version["__version__"]:
        return True

    return False


def is_phab_and_dagit_only():
    branch_name = os.getenv("BUILDKITE_BRANCH")
    if branch_name is None:
        branch_name = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    if not branch_name.startswith("phabricator"):
        return False

    try:
        base_branch = branch_name.replace("/diff/", "/base/")
        subprocess.check_call(["git", "fetch", "--tags"])
        diff_files = (
            str(subprocess.check_output(["git", "diff", base_branch, branch_name, "--name-only"]))
            .strip("'b\n")
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
