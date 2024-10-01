from pathlib import Path
from typing import List

from dagster_buildkite.git import ChangedFiles
from dagster_buildkite.package_spec import PackageSpec
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.utils import CommandStep, is_feature_branch


def skip_if_no_dagster_ui_components_changes():
    if not is_feature_branch():
        return None

    # If anything changes in the ui-components directory
    if any(
        Path("js_modules/dagster-ui/packages/ui-components") in path.parents
        for path in ChangedFiles.all
    ):
        return None

    return "No changes that affect the ui-components JS library"


def build_dagster_ui_components_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":typescript: dagster-ui-components")
        .run(
            "cd js_modules/dagster-ui/packages/ui-components",
            "pip install -U uv",
            f"tox -vv -e {AvailablePythonVersion.to_tox_factor(AvailablePythonVersion.get_default())}",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .with_skip(skip_if_no_dagster_ui_components_changes())
        .build(),
    ]


def skip_if_no_dagster_ui_core_changes():
    if not is_feature_branch():
        return None

    # If anything changes in the js_modules directory
    if any(Path("js_modules") in path.parents for path in ChangedFiles.all):
        return None

    # If anything changes in python packages that our front end depend on
    # dagster and dagster-graphql might indicate changes to our graphql schema
    if not PackageSpec("python_modules/dagster-graphql").skip_reason:
        return None

    return "No changes that affect the JS webapp"


def build_dagster_ui_core_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":typescript: dagster-ui-core")
        .run(
            "cd js_modules/dagster-ui",
            "pip install -U uv",
            f"tox -vv -e {AvailablePythonVersion.to_tox_factor(AvailablePythonVersion.get_default())}",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .with_skip(skip_if_no_dagster_ui_core_changes())
        .build(),
    ]


def skip_if_no_dagster_ui_changes():
    return skip_if_no_dagster_ui_components_changes() or skip_if_no_dagster_ui_core_changes()
