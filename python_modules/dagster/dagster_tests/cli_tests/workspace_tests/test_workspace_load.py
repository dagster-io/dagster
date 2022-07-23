import os
from tempfile import TemporaryDirectory

import pytest

from dagster import DagsterInstance
from dagster._check import CheckError
from dagster._utils import touch_file
from dagster.core.workspace.load import load_workspace_process_context_from_yaml_paths


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
            with load_workspace_process_context_from_yaml_paths(
                DagsterInstance.ephemeral(), [os.path.join(temp_dir, "foo.yaml")]
            ):
                pass
