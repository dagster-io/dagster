import os

import pytest

from dagster.check import CheckError
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.core.host_representation.handle import UserProcessApi
from dagster.seven import TemporaryDirectory
from dagster.utils import touch_file


@pytest.mark.parametrize(
    "python_user_process_api", [UserProcessApi.CLI, UserProcessApi.GRPC],
)
def test_bad_workspace_yaml_load(python_user_process_api):
    with TemporaryDirectory() as temp_dir:
        touch_file(os.path.join(temp_dir, "foo.yaml"))

        with pytest.raises(
            CheckError,
            match=(
                "Invariant failed. Description: Could not parse a workspace config from the "
                "yaml file at"
            ),
        ):
            load_workspace_from_yaml_paths(
                [os.path.join(temp_dir, "foo.yaml")], python_user_process_api
            )
