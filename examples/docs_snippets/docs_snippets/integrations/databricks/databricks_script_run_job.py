from dagster_pipes import (
    PipesCliArgsParamsLoader,
    PipesUnityCatalogVolumesContextLoader,
    PipesUnityCatalogVolumesMessageWriter,
    open_dagster_pipes,
)

if __name__ == "__main__":
    with open_dagster_pipes(
        context_loader=PipesUnityCatalogVolumesContextLoader(),
        message_writer=PipesUnityCatalogVolumesMessageWriter(),
        params_loader=PipesCliArgsParamsLoader(),
    ) as pipes:
        some_parameter = pipes.get_extra("some_parameter")
        pipes.log.info(f"Running with some_parameter={some_parameter}")

        # ... your script logic ...

        pipes.report_asset_materialization(metadata={"row_count": 99_000})
