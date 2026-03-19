import logging
import os

from buildkite_shared.context import BuildkiteContext
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    CommandStepBuilder,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.group_step_builder import (
    GroupLeafStepConfiguration,
    GroupStepBuilder,
)
from buildkite_shared.step_builders.step_builder import StepConfiguration, is_command_step
from buildkite_shared.utils import oss_path
from dagster_buildkite.steps.packages import PackageSpec


def build_helm_steps(ctx: BuildkiteContext) -> list[StepConfiguration]:
    package_spec = PackageSpec(
        oss_path(os.path.join("helm", "dagster", "schema")),
        # run helm schema tests only once, on the latest python version
        unsupported_python_versions=AvailablePythonVersion.get_all()[:-1],
        name="dagster-helm",
        retries=2,
        force_run_fn=BuildkiteContext.has_helm_changes,
    )

    steps: list[GroupLeafStepConfiguration] = []
    steps += _build_lint_steps(package_spec, ctx)
    pkg_steps = package_spec.build_steps(ctx)
    assert len(pkg_steps) == 1
    # We're only testing the latest python version, so we only expect one step.
    # Otherwise we'd be putting a group in a group which isn't supported.
    assert is_command_step(pkg_steps[0])
    steps.append(pkg_steps[0])

    return [
        GroupStepBuilder(
            name=":helm: helm",
            key="helm",
            steps=steps,
        ).build()
    ]


def _build_lint_steps(
    package_spec: PackageSpec, ctx: BuildkiteContext
) -> list[CommandStepConfiguration]:
    return [
        CommandStepBuilder("dagster-json-schema")
        .on_test_image()
        .run(
            f"pip install -e {oss_path('helm/dagster/schema')}",
            "dagster-helm schema apply",
            "git diff --exit-code",
        )
        .skip(_get_helm_step_skip_reason(ctx) and package_spec.get_skip_reason(ctx))
        .build(),
        CommandStepBuilder(":lint-roller: dagster")
        .on_test_image()
        .run(
            f"helm lint {oss_path('helm/dagster')} --with-subcharts --strict",
        )
        .skip(_get_helm_step_skip_reason(ctx) or package_spec.get_skip_reason(ctx))
        .with_retry(2)
        .build(),
        CommandStepBuilder("dagster dependency build")
        .on_test_image()
        # https://github.com/dagster-io/dagster/issues/8167
        .run(
            "helm repo add bitnami-pre-2022"
            " https://raw.githubusercontent.com/bitnami/charts/eb5f9a9513d987b519f0ecd732e7031241c50328/bitnami",
            f"helm dependency build {oss_path('helm/dagster')}",
        )
        .skip(_get_helm_step_skip_reason(ctx) and package_spec.get_skip_reason(ctx))
        .build(),
    ]


def _get_helm_step_skip_reason(ctx: BuildkiteContext) -> str | None:
    if ctx.config.no_skip:
        return None

    if not ctx.is_feature_branch:
        return None

    if ctx.has_helm_changes():
        logging.info("Run helm steps because files in the helm directory changed")
        return None

    return "No helm changes"
