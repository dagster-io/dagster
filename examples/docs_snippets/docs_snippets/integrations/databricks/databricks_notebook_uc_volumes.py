from dagster_pipes import (
    PipesDatabricksNotebookWidgetsParamsLoader,
    PipesUnityCatalogVolumesContextLoader,
    PipesUnityCatalogVolumesMessageWriter,
    open_dagster_pipes,
)

with open_dagster_pipes(
    context_loader=PipesUnityCatalogVolumesContextLoader(),
    message_writer=PipesUnityCatalogVolumesMessageWriter(),
    params_loader=PipesDatabricksNotebookWidgetsParamsLoader(dbutils.widgets),  # noqa: F821
) as pipes:
    # Access parameters passed from Dagster
    some_parameter = pipes.get_extra("some_parameter")
    pipes.log.info(f"Running with some_parameter={some_parameter}")

    # ... your notebook computation ...

    # Report structured metadata back to Dagster
    pipes.report_asset_materialization(
        metadata={
            "row_count": {"raw_value": 99_000, "type": "int"},
            "output_table": {"raw_value": "catalog.schema.output", "type": "text"},
        }
    )
