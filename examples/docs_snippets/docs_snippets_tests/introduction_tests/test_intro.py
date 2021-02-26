from dagster import execute_pipeline
from dagster.utils import script_relative_path
from docs_snippets.introduction.intro import sugariest_pipeline
from pandas import DataFrame


def test_intro_pipeline():
    cereals_path = script_relative_path(
        "../../../docs_snippets/docs_snippets/introduction/cereal.csv"
    )
    result = execute_pipeline(
        sugariest_pipeline,
        run_config={
            "solids": {
                "sugar_by_volume": {"inputs": {"cereals": {"csv": {"path": cereals_path}}}},
                "sugariest_cereals": {
                    "outputs": [{"result": {"csv": {"path": "sugariest_cereal.csv"}}}]
                },
            },
        },
    )
    assert result.success
    result_value = result.result_for_solid("sugariest_cereals").output_value()
    assert isinstance(result_value, DataFrame)
    assert list(result_value.columns) == ["name", "sugar_per_cup"]
    assert result_value.shape == (19, 2)
