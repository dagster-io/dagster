import pytest

from docs_snippets.guides.dagster.dagster_pipes.subprocess.custom_messages.dagster_code import (
    defs as custom_msg_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_1.dagster_code import (
    defs as part_1_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_1.dagster_code import (
    defs as part_2_step_1_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_2.dagster_code import (
    defs as part_2_step_2_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_3_check.dagster_code import (
    defs as part_2_step_3_check_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_3_materialization.dagster_code import (
    defs as part_2_step_3_materialization_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.with_asset_check.dagster_code import (
    defs as with_asset_check_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.with_extras_env.dagster_code import (
    defs as with_extras_env_defs,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.with_multi_asset.dagster_code import (
    defs as with_multi_asset_defs,
)


@pytest.mark.parametrize(
    "defs",
    [
        part_1_defs,
        part_2_step_1_defs,
        part_2_step_2_defs,
        part_2_step_3_check_defs,
        part_2_step_3_materialization_defs,
        with_asset_check_defs,
        with_extras_env_defs,
        with_multi_asset_defs,
        custom_msg_defs,
    ],
)
def test_execute(defs):
    job_defs = defs.get_all_job_defs()
    for job_def in job_defs:
        result = job_def.execute_in_process()
        assert result.success
