from typing import List

from dagster_buildkite.package_spec import PackageSpec
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.steps.packages import (
    _get_uncustomized_pkg_roots,
    build_steps_from_package_specs,
    gcp_creds_extra_cmds,
)
from dagster_buildkite.utils import BuildkiteStep, BlockStep
from dagster_buildkite.step_builder import CommandStepBuilder


def build_prerelease_package_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    packages = _get_uncustomized_pkg_roots("python_modules", []) + _get_uncustomized_pkg_roots(
        "python_modules/libraries", []
    )

    input_step: BlockStep = {
        "block": ":question: Choose package",
        "prompt": None,
        "fields": [
            {
                "select": "Select a package to publish",
                "key": "package-to-release-path",
                "options": [{"label": package[len("python_modules/"):], "value": package} for package in packages],
                "hint": None,
                "default": None,
                "required": True,
                "multiple": None,
            },
            {
                "text": "Enter the version to publish",
                "required": False,
                "key": "version-to-release",
                "default": None,
                "hint": "Leave blank to auto-increment the minor version",
            }
        ],
    }
    steps.append(input_step)

    steps.append(  CommandStepBuilder(":package: Build and publish package")
        .run(
            "pip install build",
            "sh ./scripts/build_and_publish.sh",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .build(),
    )



    return steps
