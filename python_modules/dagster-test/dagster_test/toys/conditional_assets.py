import random

from dagster import Output, asset


@asset(output_required=False)
def may_not_materialize(context):
    random.seed()
    rand_num = random.randint(1, 10)
    context.log.info(
        f"Random number is {rand_num}. Asset will {'not' if rand_num >=5 else ''} materialize."
    )
    if rand_num < 5:
        yield Output([1, 2, 3])


@asset
def downstream_conditional(may_not_materialize):
    return may_not_materialize + [4]
