import shutil

import pandas as pd

import dagster as dg


@dg.asset
def subprocess_asset(
    context: dg.AssetExecutionContext,
    pipes_subprocess_client: dg.PipesSubprocessClient,
) -> dg.Output[pd.DataFrame]:
    cmd = [shutil.which("python"), dg.file_relative_path(__file__, "external_code.py")]
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
    return dg.Output(
        value=summary_df,
        metadata=metadata,
    )


@dg.definitions
def resources():
    return dg.Definitions(
        resources={"pipes_subprocess_client": dg.PipesSubprocessClient()}
    )
