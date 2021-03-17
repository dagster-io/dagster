"""isort:skip_file"""

from dagster import DagsterType, InputDefinition, OutputDefinition, solid


# start_basic_even_type
EvenDagsterType = DagsterType(
    name="EvenDagsterType",
    type_check_fn=lambda _, value: isinstance(value, int) and value % 2 is 0,
)
# end_basic_even_type


# start_basic_even_type_no_annotations
@solid(
    input_defs=[InputDefinition("num", EvenDagsterType)],
    output_defs=[OutputDefinition(EvenDagsterType)],
)
def double_even(_, num):
    return num


# end_basic_even_type_no_annotations

# start_basic_even_type_with_annotations
@solid
def double_even_with_annotations(_, num: EvenDagsterType) -> EvenDagsterType:
    # These type annotations are a shorthand for constructing InputDefinitions
    # and OutputDefinitions, and are not mypy compliant
    return num  # at runtime this is a python int


# end_basic_even_type_with_annotations


# start_test_dagster_type
from dagster import check_dagster_type, Dict, Any


def test_dagster_type():

    assert check_dagster_type(Dict[Any, Any], {"foo": "bar"}).success


# end_test_dagster_type
