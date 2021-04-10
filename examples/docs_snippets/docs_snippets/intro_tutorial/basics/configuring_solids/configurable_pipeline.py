# start_pipeline_marker
import csv
import pathlib

from dagster import execute_pipeline, pipeline, solid


@solid(config_schema={"csv_name": str})
def read_csv(context):
    csv_path = pathlib.Path(__file__).parent / context.solid_config["csv_name"]
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info(f"Read {len(lines)} lines")
    return lines


@solid
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(
        cereals, key=lambda cereal: int(cereal["calories"])
    )

    context.log.info(f'Most caloric cereal: {sorted_cereals[-1]["name"]}')


@pipeline
def configurable_pipeline():
    sort_by_calories(read_csv())


# end_pipeline_marker

if __name__ == "__main__":
    # start_run_config_marker
    run_config = {
        "solids": {"read_csv": {"config": {"csv_name": "cereal.csv"}}}
    }
    # end_run_config_marker
    # start_execute_marker
    result = execute_pipeline(configurable_pipeline, run_config=run_config)
    # end_execute_marker
    assert result.success
