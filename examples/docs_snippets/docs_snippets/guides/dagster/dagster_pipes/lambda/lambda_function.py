from dagster_pipes import PipesMappingParamsLoader, open_dagster_pipes


def lambda_handler(event, _context):
    with open_dagster_pipes(
        params_loader=PipesMappingParamsLoader(event),
    ) as pipes:
        # Get some_parameter_value from the event payload
        some_parameter_value = event["some_parameter_value"]

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
