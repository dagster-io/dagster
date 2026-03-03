import logging
import os
from collections.abc import Sequence

from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.utils import dump_pipeline_yaml

# Configure logging based on LOGLEVEL env var (default to WARNING)
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOGLEVEL", "WARNING").upper(), logging.WARNING),
    format="%(levelname)s: %(message)s",
)

from buildkite_shared.context import BuildkiteContext
from dagster_buildkite.pipelines.dagster_oss_main import build_dagster_oss_main_steps
from dagster_buildkite.pipelines.dagster_oss_nightly_pipeline import build_dagster_oss_nightly_steps
from dagster_buildkite.pipelines.prerelease_package import build_prerelease_package_steps

CLI_HELP = """This CLI is used for generating Buildkite YAML. Each function corresponds to an entry
point defined in `setup.py`. Buildkite invokes these entry points when loading the specification for
a pipeline.
"""


def dagster() -> None:
    ctx = BuildkiteContext.create()
    steps = build_dagster_oss_main_steps(ctx)
    pipeline = _build_pipeline(steps)
    print(dump_pipeline_yaml(pipeline))  # noqa: T201


def dagster_nightly() -> None:
    ctx = BuildkiteContext.create()
    steps = build_dagster_oss_nightly_steps(ctx)
    pipeline = _build_pipeline(steps)
    print(dump_pipeline_yaml(pipeline))  # noqa: T201


def prerelease_package() -> None:
    ctx = BuildkiteContext.create()
    steps = build_prerelease_package_steps(ctx)
    pipeline = _build_pipeline(steps, custom_slack_channel="eng-buildkite-nightly")
    print(dump_pipeline_yaml(pipeline))  # noqa: T201


# ########################
# ##### HELPERS
# ########################

BUILD_CREATOR_EMAIL_TO_SLACK_CHANNEL_MAP = {
    "rex@dagsterlabs.com": "eng-buildkite-rex",
    "dish@dagsterlabs.com": "eng-buildkite-dish",
    "johann@dagsterlabs.com": "eng-buildkite-johann",
}


def _build_pipeline(
    steps: Sequence[StepConfiguration], custom_slack_channel: str | None = None
) -> dict[str, object]:
    return {
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
                "if": (f"build.creator.email == '{buildkite_email}'  && build.state != 'canceled'"),
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
    }
