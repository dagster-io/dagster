from pathlib import Path

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    CommandStepBuilder,
    CommandStepConfiguration,
)
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.steps.packages import PackageSpec


def skip_if_no_dagster_ui_components_changes(ctx: BuildkiteContext):
    if not ctx.is_feature_branch:
        return None

    # If anything changes in the ui-components directory
    if any(Path("js_modules/ui-components") in path.parents for path in ctx.all_changed_oss_files):
        return None

    return "No changes that affect the ui-components JS library"


def build_dagster_ui_components_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":typescript: dagster-ui-components"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "cd js_modules/ui-components",
            "pip install -U uv",
            f"tox -vv -e {AvailablePythonVersion.to_tox_factor(AvailablePythonVersion.get_default())}",
        )
        .skip(skip_if_no_dagster_ui_components_changes(ctx))
        .build(),
    ]


def skip_if_no_dagster_ui_core_changes(ctx: BuildkiteContext):
    if not ctx.is_feature_branch:
        return None

    # If anything changes in the js_modules directory
    if any(Path("js_modules") in path.parents for path in ctx.all_changed_oss_files):
        return None

    # If anything changes in python packages that our front end depend on
    # dagster and dagster-graphql might indicate changes to our graphql schema
    if not PackageSpec("python_modules/dagster-graphql").get_skip_reason(ctx):
        return None

    return "No changes that affect the JS webapp"


def build_dagster_ui_core_steps(ctx: BuildkiteContext) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":typescript: dagster-ui-core"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "cd js_modules",
            "pip install -U uv",
            f"tox -vv -e {AvailablePythonVersion.to_tox_factor(AvailablePythonVersion.get_default())}",
        )
        .skip(skip_if_no_dagster_ui_core_changes(ctx))
        .build(),
    ]


def skip_if_no_dagster_ui_changes(ctx: BuildkiteContext):
    return skip_if_no_dagster_ui_components_changes(ctx) or skip_if_no_dagster_ui_core_changes(ctx)
