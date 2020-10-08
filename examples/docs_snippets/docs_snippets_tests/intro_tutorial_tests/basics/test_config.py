from collections import OrderedDict

from docs_snippets.intro_tutorial.basics.e02_solids.config import config_pipeline

from dagster import execute_pipeline
from dagster.utils import pushd, script_relative_path


def test_tutorial_config_schema():
    with pushd(script_relative_path("../../../docs_snippets/intro_tutorial/basics/e02_solids/")):
        result = execute_pipeline(
            config_pipeline,
            run_config={
                "solids": {
                    "read_csv": {"inputs": {"csv_path": {"value": "cereal.csv"}}},
                    "sort_by_calories": {"config": {"reverse": False}},
                }
            },
        )

    assert result.success
    assert len(result.solid_result_list) == 2
    assert isinstance(result.result_for_solid("sort_by_calories").output_value(), dict)
    assert result.result_for_solid("sort_by_calories").output_value() == {
        "least_caloric": OrderedDict(
            [
                ("name", "All-Bran with Extra Fiber"),
                ("mfr", "K"),
                ("type", "C"),
                ("calories", "50"),
                ("protein", "4"),
                ("fat", "0"),
                ("sodium", "140"),
                ("fiber", "14"),
                ("carbo", "8"),
                ("sugars", "0"),
                ("potass", "330"),
                ("vitamins", "25"),
                ("shelf", "3"),
                ("weight", "1"),
                ("cups", "0.5"),
                ("rating", "93.704912"),
            ]
        ),
        "most_caloric": OrderedDict(
            [
                ("name", "Mueslix Crispy Blend"),
                ("mfr", "K"),
                ("type", "C"),
                ("calories", "160"),
                ("protein", "3"),
                ("fat", "2"),
                ("sodium", "150"),
                ("fiber", "3"),
                ("carbo", "17"),
                ("sugars", "13"),
                ("potass", "160"),
                ("vitamins", "25"),
                ("shelf", "3"),
                ("weight", "1.5"),
                ("cups", "0.67"),
                ("rating", "30.313351"),
            ]
        ),
    }
    return result
