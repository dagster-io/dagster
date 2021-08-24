from dagster import execute_pipeline

from ..connecting_solids.complex_pipeline import (
    complex_pipeline,
    find_highest_calorie_cereal,
)


# start_solid_test
def test_find_highest_calorie_cereal():
    cereals = [
        {"name": "hi-cal cereal", "calories": 400},
        {"name": "lo-cal cereal", "calories": 50},
    ]
    result = find_highest_calorie_cereal(cereals)
    assert result == "hi-cal cereal"


# end_solid_test

# start_pipeline_test
def test_complex_pipeline():
    res = execute_pipeline(complex_pipeline)
    assert res.success
    highest_protein_cereal = res.result_for_solid(
        "find_highest_protein_cereal"
    ).output_value()
    assert highest_protein_cereal == "Special K"


# end_pipeline_test
