from dagster import ModeDefinition, PresetDefinition, fs_io_manager, pipeline
from dagster_slack import slack_resource

from .resources import mock_slack_resource, postgres
from .solids import (
    analyze_cereals,
    download_file,
    load_cereals_from_csv,
    post_plot_to_slack,
    run_cereals_models,
    test_cereals_models,
)

CEREALS_DATASET_URL = "https://gist.githubusercontent.com/mgasner/bd2c0f66dff4a9f01855cfa6870b1fce/raw/2de62a57fb08da7c58d6480c987077cf91c783a1/cereal.csv"

# start_pipeline_marker_0
@pipeline(
    mode_defs=[
        ModeDefinition(
            name="prod",
            resource_defs={
                "db": postgres,
                "slack": slack_resource,
                "io_manager": fs_io_manager,
            },
        ),
        ModeDefinition(
            name="dev",
            resource_defs={
                "db": postgres,
                "slack": mock_slack_resource,
                "io_manager": fs_io_manager,
            },
        ),
    ],
    preset_defs=[
        PresetDefinition(
            name="dev",
            run_config={
                "solids": {
                    "download_file": {
                        "config": {"url": CEREALS_DATASET_URL, "target_path": "cereals.csv"}
                    },
                    "post_plot_to_slack": {"config": {"channels": ["foo_channel"]}},
                },
                "resources": {
                    "db": {
                        "config": {
                            "db_url": "postgresql://dbt_example:dbt_example@localhost:5432/dbt_example"
                        }
                    },
                    "slack": {"config": {"token": "nonce"}},
                },
            },
            mode="dev",
        ),
        PresetDefinition(
            name="prod",
            run_config={
                "solids": {
                    "download_file": {
                        "config": {"url": CEREALS_DATASET_URL, "target_path": "cereals.csv"}
                    },
                    "post_plot_to_slack": {"config": {"channels": ["foo_channel"]}},
                },
                "resources": {
                    "db": {
                        "config": {
                            "db_url": "postgresql://dbt_example:dbt_example@localhost:5432/dbt_example"
                        }
                    },
                    "slack": {"config": {"token": "nonce"}},
                },
            },
            mode="prod",
        ),
    ],
)
def dbt_example_pipeline():
    loaded = load_cereals_from_csv(download_file())
    run_results = run_cereals_models(start_after=loaded)
    test_cereals_models(start_after=run_results)
    post_plot_to_slack(analyze_cereals(run_results))


# end_pipeline_marker_0
