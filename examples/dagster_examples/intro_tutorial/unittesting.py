from dagster import execute_solid, execute_solids, lambda_solid, pipeline


@lambda_solid
def adder(num1: int, num2: int) -> int:
    return num1 + num2


@lambda_solid
def multer(num1: int, num2: int) -> int:
    return num1 * num2


@pipeline
def part_fourteen_step_one_pipeline():
    # (a + b) * (c + d)

    a_plus_b = adder.alias('a_plus_b')
    c_plus_d = adder.alias('c_plus_d')
    final = multer.alias('final')

    final(a_plus_b(), c_plus_d())


def execute_test_only_final():
    solid_result = execute_solid(
        part_fourteen_step_one_pipeline, 'final', inputs={'num1': 3, 'num2': 4}
    )
    assert solid_result.success
    assert solid_result.result_value() == 12


def execute_test_a_plus_b_final_subdag():
    results = execute_solids(
        part_fourteen_step_one_pipeline,
        ['a_plus_b', 'final'],
        inputs={'a_plus_b': {'num1': 2, 'num2': 4}, 'final': {'num2': 6}},
    )

    assert results['a_plus_b'].result_value() == 6
    assert results['final'].result_value() == 36
