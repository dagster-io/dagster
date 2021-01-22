import pandas
import requests
from dagster import Array, InputDefinition, OutputDefinition, solid
from dagster.utils import file_relative_path
from dagster_dbt import dbt_cli_run, dbt_cli_test
from dagster_dbt.cli.types import DbtCliOutput
from dagstermill import define_dagstermill_solid

CEREAL_DATASET_URL = "https://gist.githubusercontent.com/mgasner/bd2c0f66dff4a9f01855cfa6870b1fce/raw/2de62a57fb08da7c58d6480c987077cf91c783a1/cereal.csv"

PROFILES_DIR = "~/.dbt"
PROJECT_DIR = file_relative_path(__file__, "../dbt_example_project")


@solid(config_schema={"url": str, "target_path": str})
def download_file(context) -> str:

    url = context.solid_config["url"]
    target_path = context.solid_config["target_path"]

    with open(target_path, "w") as fd:
        fd.write(requests.get(url).text)

    return target_path


@solid(required_resource_keys={"db"})
def load_cereals_from_csv(context, csv_file_path):
    cereals_df = pandas.read_csv(csv_file_path)
    with context.resources.db.connect() as conn:
        conn.execute("drop table if exists cereals cascade")
        cereals_df.to_sql(name="cereals", con=conn)


@solid(config_schema={"channels": Array(str)}, required_resource_keys={"slack"})
def post_plot_to_slack(context, plot_path):
    context.resources.slack.files_upload(
        channels=",".join(context.solid_config["channels"]), file=plot_path
    )


# start_solid_marker_0
run_cereals_models = dbt_cli_run.configured(
    config_or_config_fn={"project-dir": PROJECT_DIR, "profiles-dir": PROFILES_DIR},
    name="run_cereals_models",
)
# end_solid_marker_0

test_cereals_models = dbt_cli_test.configured(
    config_or_config_fn={"project-dir": PROJECT_DIR, "profiles-dir": PROFILES_DIR},
    name="test_cereals_models",
)


analyze_cereals = define_dagstermill_solid(
    "analyze_cereals",
    file_relative_path(__file__, "notebooks/Analyze Cereals.ipynb"),
    input_defs=[InputDefinition("run_results", dagster_type=DbtCliOutput)],
    output_defs=[OutputDefinition(str)],
    required_resource_keys={"db"},
)
