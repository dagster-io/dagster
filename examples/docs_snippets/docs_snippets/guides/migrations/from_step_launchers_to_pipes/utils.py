import dagster as dg

# start_emr_config_marker


def make_emr_params(script_path: str) -> dict:
    return {
        # very rough configuration, please adjust to your needs
        "Name": "MyJobFlow",
        "Applications": [{"Name": "Hadoop"}, {"Name": "Spark"}],
        "LogUri": "s3://your-bucket/emr/logs",
        "Steps": [
            {
                "Name": "MyStep",
                "ActionOnFailure": "CONTINUE",
                "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                        "spark-submit",
                        "--deploy-mode",
                        "cluster",
                        "--master",
                        "yarn",
                        "--files",
                        "s3://your-bucket/venv.pex",
                        "--conf",
                        "spark.pyspark.python=./venv.pex",
                        "--conf",
                        "spark.yarn.submit.waitAppCompletion=true",
                        script_path,
                    ],
                },
            },
        ],
    }


# end_emr_config_marker


# start_metadata_marker


def get_latest_output_metadata_value(
    context: dg.AssetExecutionContext, asset_key: dg.AssetKey, metadata_key: str
):
    # see https://github.com/dagster-io/dagster/issues/8521 for more details about accessing upstream metadata from downstream assets and ops

    event_log_entry = (
        context.get_step_execution_context().instance.get_latest_materialization_event(
            asset_key
        )
    )
    metadata = (
        event_log_entry.dagster_event.event_specific_data.materialization.metadata  # type: ignore
    )
    return metadata[metadata_key].value


# end_metadata_marker
