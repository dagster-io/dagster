# pylint: disable=expression-not-assigned
# one_off_type_start

from dagster import DagsterType, check_dagster_type

set_containing_1 = DagsterType(
    name="set_containing_1",
    description="A set containing the value 1. May contain any other values.",
    type_check_fn=lambda _context, obj: isinstance(obj, set) and 1 in obj,
)

check_dagster_type(set_containing_1, {1, 2}).success  # => True

# one_off_type_end

# type_factory_start


def set_has_element_type_factory(x):
    return DagsterType(
        name=f"set_containing_{x}",
        description=f"A set containing the value {x}. May contain any other values.",
        type_check_fn=lambda _context, obj: isinstance(obj, set) and x in obj,
    )


set_containing_2 = set_has_element_type_factory(2)
check_dagster_type(set_containing_2, {1, 2}).success  # => True

# type_factory_end
