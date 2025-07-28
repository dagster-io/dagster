from pathlib import Path
from typing import List

from dagster_buildkite.git import ChangedFiles
from dagster_buildkite.package_spec import PackageSpec
from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    CommandStepBuilder,
    CommandStepConfiguration,
)
from dagster_buildkite.utils import is_feature_branch
from dagster_buildkite.images.versions import add_test_image


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


def build_dagster_ui_components_steps() -> List[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":typescript: dagster-ui-components"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "cd js_modules/dagster-ui/packages/ui-components",
            "pip install -U uv",
            f"tox -vv -e {AvailablePythonVersion.to_tox_factor(AvailablePythonVersion.get_default())}",
        )
        .skip_if(skip_if_no_dagster_ui_components_changes())
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


def build_dagster_ui_core_steps() -> List[CommandStepConfiguration]:
    return [
        add_test_image(
            CommandStepBuilder(":typescript: dagster-ui-core"),
            AvailablePythonVersion.get_default(),
        )
        .run(
            "cd js_modules/dagster-ui",
            "pip install -U uv",
            f"tox -vv -e {AvailablePythonVersion.to_tox_factor(AvailablePythonVersion.get_default())}",
        )
        .skip_if(skip_if_no_dagster_ui_core_changes())
        .build(),
    ]


def skip_if_no_dagster_ui_changes():
    return (
        skip_if_no_dagster_ui_components_changes()
        or skip_if_no_dagster_ui_core_changes()
    )
