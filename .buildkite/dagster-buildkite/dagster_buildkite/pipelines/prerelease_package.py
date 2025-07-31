from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.block_step_builder import BlockStepBuilder
from buildkite_shared.step_builders.command_step_builder import CommandStepBuilder
from buildkite_shared.step_builders.step_builder import StepConfiguration
from dagster_buildkite.images.versions import add_test_image
from dagster_buildkite.steps.packages import _get_uncustomized_pkg_roots


def build_prerelease_package_steps() -> list[StepConfiguration]:
    steps: list[StepConfiguration] = []

    packages = (
        _get_uncustomized_pkg_roots("python_modules", [])
        + _get_uncustomized_pkg_roots("python_modules/libraries", [])
        + _get_uncustomized_pkg_roots("examples/experimental", [])
    )

    input_step = (
        BlockStepBuilder(
            block=":question: Choose package",
        )
        .with_prompt(
            prompt=None,
            fields=[
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
                        for package in packages
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
        )
        .build()
    )
    steps.append(input_step)

    steps.append(
        add_test_image(
            CommandStepBuilder(":package: Build and publish package").run(
                "pip install build",
                "sh ./scripts/build_and_publish.sh",
            ),
            AvailablePythonVersion.get_default(),
            env=["PYPI_TOKEN"],
        ).build()
    )

    return steps
