from dagster_dbt import dbt_cli_resource
from dagster_slack import slack_resource

from dagster import file_relative_path, fs_io_manager
from dagster._legacy import ModeDefinition, PresetDefinition, pipeline

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

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_example_project")

# start_pipeline_marker_0
@pipeline(
    mode_defs=[
        ModeDefinition(
            name="prod",
            resource_defs={
                "db": postgres,
                "slack": slack_resource,
                "io_manager": fs_io_manager,
                "dbt": dbt_cli_resource.configured(
                    {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROJECT_DIR}
                ),
            },
        ),
        ModeDefinition(
            name="dev",
            resource_defs={
                "db": postgres,
                "slack": mock_slack_resource,
                "io_manager": fs_io_manager,
                "dbt": dbt_cli_resource.configured(
                    {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROJECT_DIR}
                ),
            },
        ),
    ],
    preset_defs=[
        PresetDefinition(
            name="dev",
            run_config={
                "solids": {
                    "download_file": {
                        "config": {
                            "url": CEREALS_DATASET_URL,
                            "target_path": "cereals.csv",
                        }
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
                        "config": {
                            "url": CEREALS_DATASET_URL,
                            "target_path": "cereals.csv",
                        }
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
    run_results = run_cereals_models(after=loaded)
    test_cereals_models(after=run_results)
    post_plot_to_slack(analyze_cereals(run_results))


# end_pipeline_marker_0
