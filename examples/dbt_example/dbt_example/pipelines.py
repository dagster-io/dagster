from dagster import ModeDefinition, pipeline
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


@pipeline(
    mode_defs=[
        ModeDefinition(name="prod", resource_defs={"db": postgres, "slack": slack_resource}),
        ModeDefinition(name="dev", resource_defs={"db": postgres, "slack": mock_slack_resource}),
    ]
)
def dbt_example_pipeline():
    loaded = load_cereals_from_csv(download_file())
    run_results = run_cereals_models(start_after=loaded)
    test_cereals_models(start_after=run_results)
    post_plot_to_slack(analyze_cereals(run_results))
