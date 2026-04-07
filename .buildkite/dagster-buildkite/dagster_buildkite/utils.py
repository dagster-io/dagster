import subprocess

import packaging.version


def network_buildkite_container(network_name: str) -> list[str]:
    return [
        # Set Docker API version for compatibility with older daemons
        "export DOCKER_API_VERSION=1.41",
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
) -> list[str]:
    return [
        # Now, we grab the IP address of the target container from within the target
        # bridge network and export it; this will let the tox tests talk to the target cot.
        f"export {env_variable}=`docker inspect --format "
        f"'{{{{ .NetworkSettings.Networks.{network_name}.IPAddress }}}}' "
        f"{container_name}`"
    ]


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
    assert isinstance(parsed_version, packaging.version.Version), (
        f"Found LegacyVersion: {version_str}"
    )
    return parsed_version


def get_commit(rev: str) -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", rev]).decode("utf-8").strip()
