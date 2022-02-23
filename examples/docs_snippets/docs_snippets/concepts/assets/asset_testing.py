# pylint: disable=redefined-outer-name
from dagster import asset, build_op_context

# start_simple_asset


@asset
def my_simple_asset():
    return [1, 2, 3]


# end_simple_asset

# start_test_simple_asset


def test_my_simple_asset():
    result = my_simple_asset()
    assert result == [1, 2, 3]


# end_test_simple_asset

# start_more_complex_asset


@asset
def more_complex_asset(my_simple_asset):
    return my_simple_asset + [4, 5, 6]


# end_more_complex_asset

# start_test_more_complex_asset


def test_more_complex_asset():
    result = more_complex_asset([0])
    assert result == [0, 4, 5, 6]


# end_test_more_complex_asset

# start_with_context_asset


@asset
def uses_context(context):
    return context.resources.foo


# end_with_context_asset

# start_test_with_context_asset


def test_uses_context():
    context = build_op_context(resources={"foo": "bar"})
    result = uses_context(context)
    assert result == "bar"


# end_test_with_context_asset
