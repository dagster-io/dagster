from ..defines import SupportedPython
from ..step_builder import StepBuilder


def helm_steps():
    base_paths = "'helm/dagster/*.yml' 'helm/dagster/*.yaml'"
    base_paths_ignored = "':!:helm/dagster/templates/*.yml' ':!:helm/dagster/templates/*.yaml'"
    return [
        StepBuilder("yamllint helm")
        .run(
            "pip install yamllint",
            "yamllint -c .yamllint.yaml --strict `git ls-files {base_paths} {base_paths_ignored}`".format(
                base_paths=base_paths, base_paths_ignored=base_paths_ignored
            ),
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("validate helm schema")
        .run(
            "pip install -e python_modules/automation",
            "dagster-helm schema --command=apply",
            "git diff --exit-code",
            "helm lint helm/dagster -f helm/dagster/values.yaml",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
