import os

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
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.steps.packages import PackageSpec
from dagster_buildkite.utils import has_helm_changes, skip_if_no_helm_changes


def build_helm_steps() -> list[StepConfiguration]:
    package_spec = PackageSpec(
        os.path.join("helm", "dagster", "schema"),
        # run helm schema tests only once, on the latest python version
        unsupported_python_versions=AvailablePythonVersion.get_all()[:-1],
        name="dagster-helm",
        retries=2,
        always_run_if=has_helm_changes,
    )

    steps: list[GroupLeafStepConfiguration] = []
    steps += _build_lint_steps(package_spec)
    pkg_steps = package_spec.build_steps()
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


def _build_lint_steps(package_spec) -> list[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder("dagster-json-schema"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "pip install -e helm/dagster/schema",
            "dagster-helm schema apply",
            "git diff --exit-code",
        )
        .skip_if(skip_if_no_helm_changes() and package_spec.skip_reason)
        .build(),
        add_test_image(
            CommandStepBuilder(":lint-roller: dagster"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "helm lint helm/dagster --with-subcharts --strict",
        )
        .skip_if(skip_if_no_helm_changes() or package_spec.skip_reason)
        .with_retry(2)
        .build(),
        add_test_image(
            CommandStepBuilder("dagster dependency build"),
            AvailablePythonVersion.get_default(),
        )
        # https://github.com/dagster-io/dagster/issues/8167
        .run(
            "helm repo add bitnami-pre-2022"
            " https://raw.githubusercontent.com/bitnami/charts/eb5f9a9513d987b519f0ecd732e7031241c50328/bitnami",
            "helm dependency build helm/dagster",
        )
        .skip_if(skip_if_no_helm_changes() and package_spec.skip_reason)
        .build(),
    ]
