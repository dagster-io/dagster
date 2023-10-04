from pathlib import Path
from typing import List

from dagster_buildkite.git import ChangedFiles
from dagster_buildkite.package_spec import PackageSpec

from ..python_version import AvailablePythonVersion
from ..step_builder import CommandStepBuilder
from ..utils import CommandStep, is_feature_branch


def skip_if_no_dagster_ui_changes():
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


def build_dagster_ui_steps() -> List[CommandStep]:
    return [
        CommandStepBuilder(":typescript: dagster-ui")
        .run(
            "cd js_modules/dagster-ui",
            # Explicitly install Node 16.x because BK is otherwise running 12.x.
            # Todo: Fix BK images to use newer Node versions, remove this.
            "sudo yum install"
            " https://rpm.nodesource.com/pub_20.x/nodistro/repo/nodesource-release-nodistro-1.noarch.rpm -y",
            "sudo yum install nodejs -y --setopt=nodesource-nodejs.module_hotfixes=1",
            "tox -vv -e py310",
        )
        .on_test_image(AvailablePythonVersion.get_default())
        .with_skip(skip_if_no_dagster_ui_changes())
        .build(),
    ]
