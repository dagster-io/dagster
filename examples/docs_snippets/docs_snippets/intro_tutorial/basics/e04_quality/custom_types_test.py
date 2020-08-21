import csv
import os
import typing

from dagster import (
    DagsterType,
    Failure,
    Field,
    Selector,
    String,
    check_dagster_type,
    dagster_type_loader,
    execute_pipeline,
    pipeline,
    solid,
)


def less_simple_data_frame_type_check(_, value):
    if not isinstance(value, list):
        raise Failure(
            "LessSimpleDataFrame should be a list of dicts, got "
            "{type_}".format(type_=type(value))
        )

    fields = [field for field in value[0].keys()]

    for i in range(len(value)):
        row = value[i]
        if not isinstance(row, dict):
            raise Failure(
                "LessSimpleDataFrame should be a list of dicts, "
                "got {type_} for row {idx}".format(
                    type_=type(row), idx=(i + 1)
                )
            )
        row_fields = [field for field in row.keys()]
        if fields != row_fields:
            raise Failure(
                "Rows in LessSimpleDataFrame should have the same fields, "
                "got {actual} for row {idx}, expected {expected}".format(
                    actual=row_fields, idx=(i + 1), expected=fields
                )
            )
    return True


@dagster_type_loader(Selector({"csv": Field(String)}))
def less_simple_data_frame_loader(context, selector):
    csv_path = os.path.join(os.path.dirname(__file__), selector["csv"])
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return lines


if typing.TYPE_CHECKING:
    LessSimpleDataFrame = list
else:
    LessSimpleDataFrame = DagsterType(
        name="LessSimpleDataFrame",
        description="A more sophisticated data frame that type checks its structure.",
        type_check_fn=less_simple_data_frame_type_check,
        loader=less_simple_data_frame_loader,
    )


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
    execute_pipeline(
        custom_type_pipeline,
        {
            "solids": {
                "sort_by_calories": {
                    "inputs": {"cereals": {"csv": "cereal.csv"}}
                }
            }
        },
    )


def test_less_simple_data_frame():
    assert check_dagster_type(
        LessSimpleDataFrame, [{"foo": 1}, {"foo": 2}]
    ).success

    type_check = check_dagster_type(
        LessSimpleDataFrame, [{"foo": 1}, {"bar": 2}]
    )
    assert not type_check.success
    assert type_check.description == (
        "Rows in LessSimpleDataFrame should have the same fields, "
        "got ['bar'] for row 2, expected ['foo']"
    )
