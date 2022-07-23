import pytest

from dagster import DagsterTypeCheckDidNotPass
from docs_snippets.concepts.types.types import test_dagster_type


def test_basic_even_type():
    from docs_snippets.concepts.types.types import double_even

    double_even(num=2)

    with pytest.raises(DagsterTypeCheckDidNotPass):
        double_even(num=3)


def test_basic_even_type_with_annotations():
    from docs_snippets.concepts.types.types import double_even_with_annotations

    double_even_with_annotations(num=2)

    with pytest.raises(DagsterTypeCheckDidNotPass):
        double_even_with_annotations(num=3)


def test_python_object_dagster_type():
    from docs_snippets.concepts.types.object_type import EvenType, double_even

    double_even(even_num=EvenType(2))
    with pytest.raises(AssertionError):
        double_even(even_num=EvenType(3))


def test_unit_test():
    test_dagster_type()
