from dagster.tutorials.intro_tutorial.unittesting import (
    execute_test_only_final,
    execute_test_a_plus_b_final_subdag,
)


def test_only_final():
    solid_result = execute_test_only_final()
    assert solid_result.success
    assert solid_result.transformed_value() == 12


def test_a_plus_b_final_subdag():
    results = execute_test_a_plus_b_final_subdag()
    assert results['a_plus_b'].transformed_value() == 6
    assert results['final'].transformed_value() == 36
