import dagster as dg


def test_description_inference():
    decorators = [dg.job, dg.op, dg.graph, dg.resource]
    for decorator in decorators:

        @decorator
        def my_thing():
            """Here is some
            multiline description.
            """

        assert my_thing.description == "\n".join(["Here is some", "multiline description."])  # pyright: ignore[reportFunctionMemberAccess]
