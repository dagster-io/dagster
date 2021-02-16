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
        StepBuilder(":helm: dagster-umbrella-chart :lint-roller:")
        .run(
            "pip install -e helm/dagster/schema",
            "dagster-helm schema apply",
            "git diff --exit-code",
            "helm lint helm/dagster",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":helm: dagster-user-code-deployments-chart :lint-roller:")
        .run(
            "helm lint helm/dagster/charts/dagster-user-deployments",
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
    ).get_tox_build_steps()

    return tests
