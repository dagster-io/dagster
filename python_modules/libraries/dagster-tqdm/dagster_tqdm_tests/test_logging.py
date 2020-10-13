from dagster_tqdm import dagster_tqdm

from dagster import execute_solid, solid


def test_tqdm_logging():
    called = {}

    @solid
    def tqdm_solid(context):
        for _ in dagster_tqdm(range(5), context=context, postfix="Gotta go fast!"):
            pass
        called["yup"] = True

    result = execute_solid(tqdm_solid)

    assert called["yup"]
    assert result.success
