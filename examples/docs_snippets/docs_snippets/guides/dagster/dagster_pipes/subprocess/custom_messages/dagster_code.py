import shutil

import pandas as pd

from dagster import (
    AssetExecutionContext,
    Definitions,
    Output,
    PipesSubprocessClient,
    asset,
    file_relative_path,
)


@asset
def subprocess_asset(
    context: AssetExecutionContext,
    pipes_subprocess_client: PipesSubprocessClient,
) -> Output[pd.DataFrame]:
    cmd = [shutil.which("python"), file_relative_path(__file__, "external_code.py")]
    result = pipes_subprocess_client.run(
        command=cmd,
        context=context,
    )

    # a small summary table gets reported as a custom message
    messages = result.get_custom_messages()
    if len(messages) != 1:
        raise Exception("summary not reported")

    summary_df = pd.DataFrame(messages[0])

    # grab any reported metadata off of the materialize result
    metadata = result.get_materialize_result().metadata

    # return the summary table to be loaded by Dagster for downstream assets
    return Output(
        value=summary_df,
        metadata=metadata,
    )


defs = Definitions(
    assets=[subprocess_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
