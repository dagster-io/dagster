import logging
import subprocess
from collections.abc import Sequence
from pathlib import Path

import packaging.version
import yaml
from buildkite_shared.context import BuildkiteContext
from buildkite_shared.step_builders.step_builder import StepConfiguration

BUILD_CREATOR_EMAIL_TO_SLACK_CHANNEL_MAP = {
    "rex@dagsterlabs.com": "eng-buildkite-rex",
    "dish@dagsterlabs.com": "eng-buildkite-dish",
    "johann@dagsterlabs.com": "eng-buildkite-johann",
}

# ########################
# ##### FUNCTIONS
# ########################


def buildkite_yaml_for_steps(
    steps: Sequence[StepConfiguration], custom_slack_channel: str | None = None
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

    version: dict[str, object] = {}
    with open("python_modules/dagster/dagster/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    if git_tag == version["__version__"]:
        return True

    return False


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


def get_commit(rev):
    return subprocess.check_output(["git", "rev-parse", "--short", rev]).decode("utf-8").strip()


def skip_if_no_python_changes(ctx: BuildkiteContext, overrides: Sequence[str] | None = None):
    if ctx.config.no_skip:
        return None

    if not ctx.is_feature_branch:
        return None

    if any(path.suffix == ".py" for path in ctx.all_changed_oss_files):
        return None

    if overrides and any(
        Path(override) in path.parents
        for override in overrides
        for path in ctx.all_changed_oss_files
    ):
        return None

    return "No python changes"


def skip_if_no_pyright_requirements_txt_changes(ctx: BuildkiteContext):
    if ctx.config.no_skip:
        return None

    if not ctx.is_feature_branch:
        return None

    if any(path.match("pyright/*/requirements.txt") for path in ctx.all_changed_oss_files):
        return None

    return "No pyright requirements.txt changes"


def skip_if_no_yaml_changes(ctx: BuildkiteContext):
    if ctx.config.no_skip:
        return None

    if not ctx.is_feature_branch:
        return None

    if any(path.suffix in [".yml", ".yaml"] for path in ctx.all_changed_oss_files):
        return None

    return "No yaml changes"


def skip_if_no_non_docs_markdown_changes(ctx: BuildkiteContext):
    if ctx.config.no_skip:
        return None

    if not ctx.is_feature_branch:
        return None

    if any(
        path.suffix == ".md" and Path("dagster-oss/docs") not in path.parents
        for path in ctx.all_changed_oss_files
    ):
        return None

    return "No markdown changes outside of docs"


def has_helm_changes(ctx: BuildkiteContext) -> bool:
    return any(Path("helm") in path.parents for path in ctx.all_changed_oss_files)


def has_dagster_airlift_changes(ctx: BuildkiteContext) -> bool:
    return any("dagster-airlift" in str(path) for path in ctx.all_changed_oss_files)


def has_dg_changes(ctx: BuildkiteContext) -> bool:
    return any(
        "dagster-dg" in str(path) or "docs_snippets" in str(path)
        for path in ctx.all_changed_oss_files
    )


def has_component_integration_changes(ctx: BuildkiteContext) -> bool:
    """Check for changes in integrations that implement components."""
    component_integrations = [
        "dagster-sling",
        "dagster-dbt",
        "dagster-databricks",
        "dagster-airbyte",
        "dagster-powerbi",
        "dagster-omni",
        "dagster-polytomic",
        "dagster-fivetran",
        "dagster-dlt",
    ]
    return any(
        any(integration in str(path) for integration in component_integrations)
        for path in ctx.all_changed_oss_files
    )


def has_storage_test_fixture_changes(ctx: BuildkiteContext) -> bool:
    # Attempt to ensure that changes to TestRunStorage and TestEventLogStorage suites trigger integration
    return any(
        Path("python_modules/dagster/dagster_tests/storage_tests/utils") in path.parents
        for path in ctx.all_changed_oss_files
    )


def skip_if_not_dagster_dbt_cloud_commit(ctx: BuildkiteContext) -> str | None:
    """If no dagster-dbt cloud v2 files are touched, then do NOT run. Even if on master."""
    return (
        None
        if (
            any("dagster_dbt/cloud_v2" in str(path) for path in ctx.all_changed_oss_files)
            # The kitchen sink in dagster-dbt in only testing the dbt Cloud integration v2.
            # Do not skip tests if changes are made to this test suite.
            or any("dagster-dbt/kitchen-sink" in str(path) for path in ctx.all_changed_oss_files)
        )
        else "Not a dagster-dbt Cloud commit"
    )


def skip_if_not_dagster_dbt_commit(ctx: BuildkiteContext) -> str | None:
    """If no dagster-dbt files are touched, then do NOT run. Even if on master."""
    return (
        None
        if (any("dagster_dbt" in str(path) for path in ctx.all_changed_oss_files))
        else "Not a dagster-dbt commit"
    )


def skip_if_no_helm_changes(ctx: BuildkiteContext):
    if ctx.config.no_skip:
        return None

    if not ctx.is_feature_branch:
        return None

    if has_helm_changes(ctx):
        logging.info("Run helm steps because files in the helm directory changed")
        return None

    return "No helm changes"


def skip_if_no_docs_changes(ctx: BuildkiteContext):
    if ctx.config.no_skip:
        return None

    if "BUILDKITE_DOCS" in ctx.message:
        return None

    if not ctx.is_feature_branch:
        return None

    # If anything changes in the docs directory
    if any(Path("dagster-oss/docs") in path.parents for path in ctx.all_changed_oss_files):
        logging.info("Run docs steps because files in the dagster-oss/docs directory changed")
        return None

    # If anything changes in the examples directory. This is where our docs snippets live.
    if any(Path("dagster-oss/examples") in path.parents for path in ctx.all_changed_oss_files):
        logging.info("Run docs steps because files in the dagster-oss/examples directory changed")
        return None

    return "No docs changes"
