import csv
import os
import typing

import dagster as dg


def less_simple_data_frame_type_check(_, value):
    if not isinstance(value, list):
        raise dg.Failure(
            f"LessSimpleDataFrame should be a list of dicts, got {type(value)}"
        )

    fields = [field for field in value[0].keys()]

    for i in range(len(value)):
        row = value[i]
        if not isinstance(row, dict):
            raise dg.Failure(
                f"LessSimpleDataFrame should be a list of dicts, got {type(row)} for row"
                f" {i + 1}"
            )
        row_fields = [field for field in row.keys()]
        if fields != row_fields:
            raise dg.Failure(
                "Rows in LessSimpleDataFrame should have the same fields, "
                f"got {row_fields} for row {i + 1}, expected {fields}"
            )
    return True


@dg.dagster_type_loader({"csv_path": dg.Field(dg.String)})
def less_simple_data_frame_loader(context, config):
    csv_path = os.path.join(os.path.dirname(__file__), config["csv_path"])
    with open(csv_path, encoding="utf8") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info(f"Read {len(lines)} lines")
    return lines


if typing.TYPE_CHECKING:
    LessSimpleDataFrame = list
else:
    LessSimpleDataFrame = dg.DagsterType(
        name="LessSimpleDataFrame",
        description="A more sophisticated data frame that type checks its structure.",
        type_check_fn=less_simple_data_frame_type_check,
        loader=less_simple_data_frame_loader,
    )


@dg.op
def sort_by_calories(context: dg.OpExecutionContext, cereals: LessSimpleDataFrame):
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


@dg.job
def custom_type_job():
    sort_by_calories()


if __name__ == "__main__":
    custom_type_job.execute_in_process(
        run_config={
            "ops": {
                "sort_by_calories": {"inputs": {"cereals": {"csv_path": "cereal.csv"}}}
            }
        },
    )


# start_custom_types_test_marker_0
def test_less_simple_data_frame():
    assert dg.check_dagster_type(LessSimpleDataFrame, [{"foo": 1}, {"foo": 2}]).success

    type_check = dg.check_dagster_type(LessSimpleDataFrame, [{"foo": 1}, {"bar": 2}])
    assert not type_check.success
    assert (
        type_check.description
        == "Rows in LessSimpleDataFrame should have the same fields, "
        "got ['bar'] for row 2, expected ['foo']"
    )


# end_custom_types_test_marker_0
