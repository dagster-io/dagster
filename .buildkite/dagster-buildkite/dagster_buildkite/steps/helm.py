import os
from typing import List

from ..defines import SupportedPython
from ..module_build_spec import ModuleBuildSpec
from ..step_builder import StepBuilder


def helm_lint_steps() -> List[dict]:
    return [
        StepBuilder(":helm: :yaml: :lint-roller:")
        .run(
            "pip install yamllint",
            "make yamllint",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":helm: dagster-json-schema")
        .run(
            "pip install -e helm/dagster/schema",
            "dagster-helm schema apply",
            "git diff --exit-code",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":helm: dagster :lint-roller:")
        .run(
            "helm lint helm/dagster --with-subcharts --strict",
        )
        .on_integration_image(SupportedPython.V3_7)
        .with_retry(1)
        .build(),
        StepBuilder(":helm: dagster dependency build")
        .run(
            "helm repo add bitnami https://charts.bitnami.com/bitnami",
            "helm dependency build helm/dagster",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]


def helm_steps() -> List[dict]:
    tests = []
    tests += helm_lint_steps()
    tests += ModuleBuildSpec(
        os.path.join("helm", "dagster", "schema"),
        buildkite_label="dagster-helm-schema",
        upload_coverage=False,
        retries=1,
    ).get_tox_build_steps()

    return tests
