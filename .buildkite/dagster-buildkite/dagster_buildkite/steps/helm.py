import os
from typing import List

from ..package_spec import PackageSpec
from ..python_version import AvailablePythonVersion
from ..step_builder import CommandStepBuilder
from ..utils import BuildkiteLeafStep, BuildkiteStep, CommandStep, GroupStep


def build_helm_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteLeafStep] = []
    steps += _build_lint_steps()
    schema_group = PackageSpec(
        os.path.join("helm", "dagster", "schema"),
        unsupported_python_versions=[
            # run helm schema tests only once, on the latest python version
            AvailablePythonVersion.V3_6,
            AvailablePythonVersion.V3_7,
            AvailablePythonVersion.V3_8,
        ],
        name="dagster-helm-schema",
        upload_coverage=False,
        retries=2,
    ).build_steps()[0]
    steps += schema_group["steps"]

    return [
        GroupStep(
            group=":helm: helm",
            key="helm",
            steps=steps,
        )
    ]


def _build_lint_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":yaml: :lint-roller:")
        .run(
            "pip install yamllint",
            "make yamllint",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
        CommandStepBuilder("dagster-json-schema")
        .run(
            "pip install -e helm/dagster/schema",
            "dagster-helm schema apply",
            "git diff --exit-code",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
        CommandStepBuilder(":lint-roller: dagster")
        .run(
            "helm lint helm/dagster --with-subcharts --strict",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .with_retry(2)
        .build(),
        CommandStepBuilder("dagster dependency build")
        # https://github.com/dagster-io/dagster/issues/8167
        .run(
            "helm repo add bitnami-pre-2022 https://raw.githubusercontent.com/bitnami/charts/eb5f9a9513d987b519f0ecd732e7031241c50328/bitnami",
            "helm dependency build helm/dagster",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
    ]
