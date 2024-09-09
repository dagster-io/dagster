from typing import List

from dagster_buildkite.package_spec import PackageSpec
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.steps.packages import (
    _get_uncustomized_pkg_roots,
    build_steps_from_package_specs,
    gcp_creds_extra_cmds,
)
from dagster_buildkite.utils import BuildkiteStep, InputStep


def build_prerelease_package_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    packages = _get_uncustomized_pkg_roots("python_modules", []) + _get_uncustomized_pkg_roots(
        "python_modules/libraries", []
    )

    input_step: InputStep = {
        "input": "foo",
        "prompt": None,
        "fields": [
            {
                "select": "Select a package to publish",
                "key": "package",
                "options": [{"label": package, "value": package} for package in packages],
                "hint": None,
                "default": None,
                "required": None,
                "multiple": None,
            }
        ],
    }
    steps.append(input_step)

    return steps
