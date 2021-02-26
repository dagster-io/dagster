import os
from typing import List

from ..defines import SupportedPython
from ..module_build_spec import ModuleBuildSpec
from ..step_builder import StepBuilder


def helm_lint_steps() -> List[dict]:
    base_paths = "'helm/dagster/*.yml' 'helm/dagster/*.yaml'"
    base_paths_ignored = "':!:helm/dagster/templates/*.yml' ':!:helm/dagster/templates/*.yaml'"
    return [
        StepBuilder(":helm: :yaml: :lint-roller:")
        .run(
            "pip install yamllint",
            f"yamllint -c .yamllint.yaml --strict `git ls-files {base_paths} {base_paths_ignored}`",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":helm: :lint-roller:")
        .run(
            "pip install -e python_modules/automation",
            "dagster-helm schema --command=apply",
            "git diff --exit-code",
            "helm lint helm/dagster -f helm/dagster/values.yaml",
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
