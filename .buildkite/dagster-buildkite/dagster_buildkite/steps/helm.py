from ..defines import SupportedPython
from ..step_builder import StepBuilder


def helm_steps():
    base_paths = "'helm/dagster/*.yml' 'helm/dagster/*.yaml'"
    base_paths_ignored = "':!:helm/dagster/templates/*.yml' ':!:helm/dagster/templates/*.yaml'"
    return [
        StepBuilder(":helm: yamllint")
        .run(
            "pip install yamllint",
            f"yamllint -c .yamllint.yaml --strict `git ls-files {base_paths} {base_paths_ignored}`",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":helm: validate schema")
        .run(
            "pip install -e python_modules/automation",
            "dagster-helm schema --command=apply",
            "git diff --exit-code",
            "helm lint helm/dagster -f helm/dagster/values.yaml",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
