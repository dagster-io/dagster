from dagster_pipes import (
    PipesDatabricksNotebookWidgetsParamsLoader,
    PipesUnityCatalogVolumesContextLoader,
    PipesUnityCatalogVolumesMessageWriter,
    open_dagster_pipes,
)

with open_dagster_pipes(
    context_loader=PipesUnityCatalogVolumesContextLoader(),
    message_writer=PipesUnityCatalogVolumesMessageWriter(),
    params_loader=PipesDatabricksNotebookWidgetsParamsLoader(dbutils.widgets),  # noqa
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
