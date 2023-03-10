from dagster import graph, job, op, resource


def test_description_inference():
    decorators = [job, op, graph, resource]
    for decorator in decorators:

        @decorator  # pylint: disable=cell-var-from-loop
        def my_thing():
            """Here is some
            multiline description.
            """

        assert my_thing.description == "\n".join(["Here is some", "multiline description."])
