# isort: skip_file

from dagster import DagsterType, In, Out, op


# start_basic_even_type
EvenDagsterType = DagsterType(
    name="EvenDagsterType",
    type_check_fn=lambda _, value: isinstance(value, int) and value % 2 is 0,
)
# end_basic_even_type


# start_basic_even_type_no_annotations
@op(
    ins={"num": In(EvenDagsterType)},
    out=Out(EvenDagsterType),
)
def double_even(num):
    return num


# end_basic_even_type_no_annotations

# start_basic_even_type_with_annotations
@op(
    ins={"num": In(EvenDagsterType)},
    out=Out(EvenDagsterType),
)
def double_even_with_annotations(num: int) -> int:
    return num


# end_basic_even_type_with_annotations


# start_auto_type


class MyClass:
    pass


@op
def my_op() -> MyClass:
    return MyClass()


# end_auto_type


# start_test_dagster_type
from dagster import check_dagster_type, Dict, Any


def test_dagster_type():

    assert check_dagster_type(Dict[Any, Any], {"foo": "bar"}).success


# end_test_dagster_type
