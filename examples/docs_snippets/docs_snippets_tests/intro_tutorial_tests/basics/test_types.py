import csv
from collections import OrderedDict

from dagster import execute_solid
from dagster.utils import script_relative_path
from docs_snippets.intro_tutorial.basics.e04_quality.custom_types_2 import (
    sort_by_calories,
)
from docs_snippets.intro_tutorial.basics.e04_quality.custom_types_4 import (
    less_simple_data_frame_type_check,
)


def test_type_check():
    res = less_simple_data_frame_type_check(None, "foo")
    assert res is False or res.success is False

    res = less_simple_data_frame_type_check(
        None, [OrderedDict([("foo", 1)]), OrderedDict([("foo", 2)])]
    )
    assert res is True or res.success is True

    res = less_simple_data_frame_type_check(
        None, [OrderedDict([("foo", 1)]), OrderedDict([("bar", 2)])]
    )
    assert res is False or res.success is False

    res = less_simple_data_frame_type_check(None, [OrderedDict([("foo", 1)]), 2])
    assert res is False or res.success is False


def test_sort():
    with open(
        script_relative_path("../../../docs_snippets/intro_tutorial/cereal.csv"),
        "r",
        encoding="utf8",
    ) as fd:
        cereals = [row for row in csv.DictReader(fd)]

    execute_solid(sort_by_calories, input_values={"cereals": cereals})
