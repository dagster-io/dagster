import os

import pytest
from dagster.check import CheckError
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.seven import TemporaryDirectory
from dagster.utils import touch_file


def test_bad_workspace_yaml_load():
    with TemporaryDirectory() as temp_dir:
        touch_file(os.path.join(temp_dir, "foo.yaml"))

        with pytest.raises(
            CheckError,
            match=(
                "Invariant failed. Description: Could not parse a workspace config from the "
                "yaml file at"
            ),
        ):
            with load_workspace_from_yaml_paths([os.path.join(temp_dir, "foo.yaml")]):
                pass
