from dagster import pipeline, solid


@solid
def adder(_, num1: int, num2: int) -> int:
    return num1 + num2


@solid
def multer(_, num1: int, num2: int) -> int:
    return num1 * num2


@pipeline
def reusing_solids_pipeline():
    # (a + b) * (c + d)

    a_plus_b = adder.alias('a_plus_b')
    c_plus_d = adder.alias('c_plus_d')
    final = multer.alias('final')

    final(a_plus_b(), c_plus_d())
