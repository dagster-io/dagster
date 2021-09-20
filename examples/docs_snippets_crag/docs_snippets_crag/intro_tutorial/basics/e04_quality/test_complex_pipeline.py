from ..connecting_solids.complex_pipeline import (
    diamond,
    find_highest_calorie_cereal,
)


# start_op_test
def test_find_highest_calorie_cereal():
    cereals = [
        {"name": "hi-cal cereal", "calories": 400},
        {"name": "lo-cal cereal", "calories": 50},
    ]
    result = find_highest_calorie_cereal(cereals)
    assert result == "hi-cal cereal"


# end_optest

# start_graph_test
def test_diamond():
    res = diamond.execute_in_process()
    assert res.success
    highest_protein_cereal = res.result_for_node(
        "find_highest_protein_cereal"
    ).output_value()
    assert highest_protein_cereal == "Special K"


# end_graph_test
