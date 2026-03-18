from buildkite_shared.context import BuildkiteContext
from buildkite_shared.step_builders.step_builder import StepConfiguration
from dagster_buildkite.steps.dagster import build_dagster_steps, build_repo_wide_steps
from dagster_buildkite.steps.dagster_ui import (
    build_dagster_ui_components_steps,
    build_dagster_ui_core_steps,
)
from dagster_buildkite.steps.docs import build_docs_steps


def build_dagster_oss_main_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    steps: list[StepConfiguration] = []

    # Note: we used to trigger an internal build (oss-internal-compatibility/internal),
    # but with monorepo, that became unnecessary because the majority of edits
    # now come from the internal repo

    # Full pipeline.
    steps += build_repo_wide_steps(ctx)
    steps += build_docs_steps(ctx)
    steps += build_dagster_ui_components_steps(ctx)
    steps += build_dagster_ui_core_steps(ctx)
    steps += build_dagster_steps(ctx)

    return steps
