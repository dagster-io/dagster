### EXTERNAL PROCESS

from dagster_pipes import (
    PipesDefaultContextLoader,
    PipesDefaultMessageWriter,
    PipesEnvVarParamsLoader,
    open_dagster_pipes,
)

# `user_code` is a fictional package providing pre-existing business logic for assets.
from user_code import get_data_version, get_metric  # type: ignore

with open_dagster_pipes(
    params_loader=PipesEnvVarParamsLoader(),
    context_loader=PipesDefaultContextLoader(),
    message_writer=PipesDefaultMessageWriter(),
) as pipes:
    # Equivalent of calling `context.log.info` on the orchestration side.
    # Streams log message back to orchestration process.
    pipes.log.info(f"materializing asset {pipes.asset_key}")

    # ... business logic

    # Creates a `MaterializeResult` on the orchestration side. Notice no value for the asset is
    # included. Pipes only supports reporting that a materialization occurred and associated
    # metadata.
    pipes.report_asset_materialization(
        metadata={"some_metric": {"raw_value": get_metric(), "type": "text"}},
        data_version=get_data_version(),
    )
