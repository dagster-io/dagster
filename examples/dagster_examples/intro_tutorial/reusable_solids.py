from dagster import lambda_solid, pipeline


@lambda_solid
def adder(num1: int, num2: int) -> int:
    return num1 + num2


@lambda_solid
def multer(num1: int, num2: int) -> int:
    return num1 * num2


@pipeline
def reusable_solids_pipeline():
    # (a + b) * (c + d)

    a_plus_b = adder.alias('a_plus_b')
    c_plus_d = adder.alias('c_plus_d')
    final = multer.alias('final')

    final(a_plus_b(), c_plus_d())
