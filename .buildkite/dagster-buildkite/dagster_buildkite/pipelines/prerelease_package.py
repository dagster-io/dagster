import re
from pathlib import Path
from typing import List

from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.steps.packages import _get_uncustomized_pkg_roots
from dagster_buildkite.utils import BlockStep, BuildkiteStep


def build_prerelease_package_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    packages = (
        _get_uncustomized_pkg_roots("python_modules", [])
        + _get_uncustomized_pkg_roots("python_modules/libraries", [])
        + _get_uncustomized_pkg_roots("examples/experimental", [])
    )

    # Get only packages that have a fixed version in setup.py
    filtered_packages = []
    for package in packages:
        setup_file = Path(package) / "setup.py"
        contents = setup_file.read_text()
        if re.findall(r"version=\"[\d\.]+\"", contents):
            filtered_packages.append(package)

    input_step: BlockStep = {
        "block": ":question: Choose package",
        "prompt": None,
        "fields": [
            {
                "select": "Select a package to publish",
                "key": "package-to-release-path",
                "options": [
                    {
                        "label": package[len("python_modules/") :]
                        if package.startswith("python_modules/")
                        else package,
                        "value": package,
                    }
                    for package in filtered_packages
                ],
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
            },
        ],
    }
    steps.append(input_step)

    steps.append(
        CommandStepBuilder(":package: Build and publish package")
        .run(
            "pip install build",
            "sh ./scripts/build_and_publish.sh",
        )
        .on_test_image(AvailablePythonVersion.get_default(), env=["PYPI_TOKEN"])
        .build()
    )

    return steps
