import pytest
from dagster import DagsterTypeCheckDidNotPass, execute_solid
from docs_snippets_crag.concepts.types.types import test_dagster_type


def test_basic_even_type():
    from docs_snippets_crag.concepts.types.types import double_even

    assert execute_solid(double_even, input_values={"num": 2}).success

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(double_even, input_values={"num": 3})

    assert not execute_solid(double_even, input_values={"num": 3}, raise_on_error=False).success


def test_basic_even_type_with_annotations():
    from docs_snippets_crag.concepts.types.types import double_even_with_annotations

    assert execute_solid(double_even_with_annotations, input_values={"num": 2}).success

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(double_even_with_annotations, input_values={"num": 3})

    assert not execute_solid(
        double_even_with_annotations, input_values={"num": 3}, raise_on_error=False
    ).success


def test_python_object_dagster_type():
    from docs_snippets_crag.concepts.types.object_type import EvenType, double_even

    assert execute_solid(double_even, input_values={"even_num": EvenType(2)}).success
    with pytest.raises(AssertionError):
        execute_solid(double_even, input_values={"even_num": EvenType(3)})


def test_usable_as_dagster_type():
    from docs_snippets_crag.concepts.types.usable_as import EvenType, double_even

    assert execute_solid(double_even, input_values={"even_num": EvenType(2)}).success


def test_make_python_type_usable_as_dagster_type():
    from docs_snippets_crag.concepts.types.make_usable import EvenType, double_even

    assert execute_solid(double_even, input_values={"even_num": EvenType(2)}).success


def test_unit_test():
    test_dagster_type()
