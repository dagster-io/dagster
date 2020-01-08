import dagster
import dagster.helpers.solid_from_func as solid_from_func


def test_sff():
    def test_func(x):
        assert x == 3

    solid = solid_from_func.solid_from_func(test_func)

    dagster.execute_solid(solid, input_values={'x': 3})

    try:
        dagster.execute_solid(solid, input_values={'x': 4})
        raise Exception('Assertion should have failed')
    except dagster.core.errors.DagsterExecutionStepExecutionError:
        pass

def test_sff_defaults_varargs():
    def test_func(x=3, *args, **kwargs):
        assert x == 3

    solid = solid_from_func.solid_from_func(test_func)

    dagster.execute_solid(solid)
