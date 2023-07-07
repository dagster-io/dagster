from typing import List

import pytest
from dagster_dbt.core.utils import _create_command_list


@pytest.mark.parametrize(
    argnames=["debug", "prefix"],
    argvalues=[
        (True, ["dbt", "--debug"]),
        (False, ["dbt"]),
    ],
    ids=["debug", "no-debug"],
)
def test_create_command_list_debug(debug: bool, prefix: List[str]):
    command_list = _create_command_list(
        executable="dbt",
        warn_error=False,
        json_log_format=False,
        command="run",
        flags_dict={},
        debug=debug,
    )
    assert command_list == prefix + ["run"]
