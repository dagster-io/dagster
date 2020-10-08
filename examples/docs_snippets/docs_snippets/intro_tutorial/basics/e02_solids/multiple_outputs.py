import csv
import os

from dagster import (
    Bool,
    Field,
    Output,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    solid,
)


@solid
def read_csv(context, csv_path):
    lines = []
    csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    with open(csv_path, "r") as fd:
        for row in csv.DictReader(fd):
            row["calories"] = int(row["calories"])
            lines.append(row)

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return lines


@solid(
    config_schema={
        "process_hot": Field(Bool, is_required=False, default_value=True),
        "process_cold": Field(Bool, is_required=False, default_value=True),
    },
    output_defs=[
        OutputDefinition(name="hot_cereals", is_required=False),
        OutputDefinition(name="cold_cereals", is_required=False),
    ],
)
def split_cereals(context, cereals):
    if context.solid_config["process_hot"]:
        hot_cereals = [cereal for cereal in cereals if cereal["type"] == "H"]
        yield Output(hot_cereals, "hot_cereals")
    if context.solid_config["process_cold"]:
        cold_cereals = [cereal for cereal in cereals if cereal["type"] == "C"]
        yield Output(cold_cereals, "cold_cereals")


# start-sort-and-pipeline
@solid
def sort_hot_cereals_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
    context.log.info(
        "Least caloric hot cereal: {least_caloric}".format(
            least_caloric=sorted_cereals[0]["name"]
        )
    )


@solid
def sort_cold_cereals_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
    context.log.info(
        "Least caloric cold cereal: {least_caloric}".format(
            least_caloric=sorted_cereals[0]["name"]
        )
    )


@pipeline
def multiple_outputs_pipeline():
    hot_cereals, cold_cereals = split_cereals(read_csv())
    sort_hot_cereals_by_calories(hot_cereals)
    sort_cold_cereals_by_calories(cold_cereals)


# end-sort-and-pipeline


if __name__ == "__main__":
    run_config = {
        "solids": {
            "read_csv": {"inputs": {"csv_path": {"value": "cereal.csv"}}}
        }
    }
    result = execute_pipeline(
        multiple_outputs_pipeline, run_config=run_config
    )
    assert result.success
