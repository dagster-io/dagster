import pytest

import dagster as dg
from docs_snippets.guides.dagster.dagster_pipes.subprocess.custom_messages.dagster_code import (
    subprocess_asset as custom_msg,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_1.dagster_code import (
    subprocess_asset as part_1,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_1.dagster_code import (
    subprocess_asset as part_2_step_1,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_2.dagster_code import (
    subprocess_asset as part_2_step_2,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_3_check.dagster_code import (
    subprocess_asset as part_2_step_3_check,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.part_2.step_3_materialization.dagster_code import (
    subprocess_asset as part_2_step_3_materialization,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.with_asset_check.dagster_code import (
    no_empty_order_check,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.with_extras_env.dagster_code import (
    subprocess_asset as with_extras_env,
)
from docs_snippets.guides.dagster.dagster_pipes.subprocess.with_multi_asset.dagster_code import (
    subprocess_asset as with_multi_asset,
)

custom_msg_defs = dg.Definitions(
    assets=[custom_msg],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

part_1_defs = dg.Definitions(
    assets=[part_1],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

part_2_step_1_defs = dg.Definitions(
    assets=[part_2_step_1],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

part_2_step_2_defs = dg.Definitions(
    assets=[part_2_step_2],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

part_2_step_3_check_defs = dg.Definitions(
    assets=[part_2_step_3_check],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

part_2_step_3_materialization_defs = dg.Definitions(
    assets=[part_2_step_3_materialization],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

with_asset_check_defs = dg.Definitions(
    assets=[no_empty_order_check],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

with_extras_env_defs = dg.Definitions(
    assets=[with_extras_env],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
)

with_multi_asset_defs = dg.Definitions(
    assets=[with_multi_asset],
    resources={"pipes_subprocess_client": dg.PipesSubprocessClient()},
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
def test_execute(defs: dg.Definitions) -> None:
    job_defs = defs.resolve_all_job_defs()
    for job_def in job_defs:
        result = job_def.execute_in_process()
        assert result.success
