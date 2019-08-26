from dagster import ExpectationResult, Output, pipeline, solid


@solid
def add_ints(_, num_one: int, num_two: int) -> int:
    yield ExpectationResult(label='num_one_positive', success=num_one > 0)

    yield Output(num_one + num_two)


@pipeline
def expectations_tutorial_pipeline():
    add_ints()  # pylint: disable=no-value-for-parameter
