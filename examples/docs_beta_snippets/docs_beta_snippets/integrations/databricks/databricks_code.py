from dagster_pipes import (
    PipesDbfsContextLoader,
    PipesDbfsMessageWriter,
    open_dagster_pipes,
)

# Sets up communication channels and downloads the context data sent from Dagster.
# Note that while other `context_loader` and `message_writer` settings are
# possible, it is recommended to use `PipesDbfsContextLoader` and
# `PipesDbfsMessageWriter` for Databricks.
with open_dagster_pipes(
    context_loader=PipesDbfsContextLoader(),
    message_writer=PipesDbfsMessageWriter(),
) as pipes:
    # Access the `extras` dict passed when launching the job from Dagster.
    some_parameter_value = pipes.get_extra("some_parameter")

    # Stream log message back to Dagster
    pipes.log.info(f"Using some_parameter value: {some_parameter_value}")

    # ... your code that computes and persists the asset

    # Stream asset materialization metadata and data version back to Dagster.
    # This should be called after you've computed and stored the asset value. We
    # omit the asset key here because there is only one asset in scope, but for
    # multi-assets you can pass an `asset_key` parameter.
    pipes.report_asset_materialization(
        metadata={
            "some_metric": {"raw_value": some_parameter_value + 1, "type": "int"}
        },
        data_version="alpha",
    )
