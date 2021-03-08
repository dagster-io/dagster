import csv
import os

from dagster import (
    DagsterType,
    Field,
    String,
    dagster_type_loader,
    execute_pipeline,
    pipeline,
    solid,
)


def less_simple_data_frame_type_check(_, value):
    if not isinstance(value, list):
        return False

    fields = [field for field in value[0].keys()]

    for i in range(len(value)):
        row = value[i]
        if not isinstance(row, dict):
            return False
        row_fields = [field for field in row.keys()]
        if fields != row_fields:
            return False
    return True


# start_custom_types_3_marker_0
@dagster_type_loader({"csv_path": Field(String)})
def less_simple_data_frame_loader(context, config):
    csv_path = os.path.join(os.path.dirname(__file__), config["csv_path"])
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return lines


# end_custom_types_3_marker_0

# start_custom_types_3_marker_1
LessSimpleDataFrame = DagsterType(
    name="LessSimpleDataFrame",
    description="A more sophisticated data frame that type checks its structure.",
    type_check_fn=less_simple_data_frame_type_check,
    loader=less_simple_data_frame_loader,
)
# end_custom_types_3_marker_1


@solid
def sort_by_calories(context, cereals: LessSimpleDataFrame):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
    context.log.info(
        "Least caloric cereal: {least_caloric}".format(
            least_caloric=sorted_cereals[0]["name"]
        )
    )
    context.log.info(
        "Most caloric cereal: {most_caloric}".format(
            most_caloric=sorted_cereals[-1]["name"]
        )
    )


@pipeline
def custom_type_pipeline():
    sort_by_calories()


if __name__ == "__main__":
    # start_custom_types_3_marker_2
    execute_pipeline(
        custom_type_pipeline,
        {
            "solids": {
                "sort_by_calories": {
                    "inputs": {"cereals": {"csv_path": "cereal.csv"}}
                }
            }
        },
    )
    # end_custom_types_3_marker_2
