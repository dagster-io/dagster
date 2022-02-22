from dagster import asset, build_op_context

# start_no_context


@asset
def simple_asset():
    return [1, 2, 3]


def test_simple_asset():
    result = simple_asset()
    assert result == [1, 2, 3]


@asset
def more_complex_asset(simple_asset):
    return simple_asset + [4, 5, 6]


def test_more_complex_asset():
    result = more_complex_asset([0])
    assert result == [0, 4, 5, 6]


# end_no_context

# start_with_context


@asset
def uses_context(context):
    return context.resources.foo


def test_uses_context():
    context = build_op_context(resources={"foo": "bar"})
    result = uses_context(context)
    assert result == "bar"


# end_with_context
