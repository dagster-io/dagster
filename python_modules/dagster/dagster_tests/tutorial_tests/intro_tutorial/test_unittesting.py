from dagster.tutorials.intro_tutorial.unittesting import (
    execute_test_only_final,
    execute_test_a_plus_b_final_subdag,
)


def test_only_final():
    execute_test_only_final()


def test_a_plus_b_final_subdag():
    execute_test_a_plus_b_final_subdag()
