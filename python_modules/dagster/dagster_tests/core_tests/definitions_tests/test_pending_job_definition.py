from dagster import ResourceDefinition, graph, op


def test_pending_job_coercion():
    @op(required_resource_keys={"foo", "bar"})
    def the_op(context):
        return context.resources.foo + context.resources.bar

    @graph
    def the_graph():
        return the_op()

    pending_job = the_graph.to_pending_job(
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("foo")}
    )

    job_def = pending_job.coerce_to_job_def(
        resource_defs={
            "bar": ResourceDefinition.hardcoded_resource("bar"),
            "foo": ResourceDefinition.hardcoded_resource("baz"),
        }
    )

    result = job_def.execute_in_process()
    assert result.success

    assert result.output_value() == "foobar"


def test_pending_job_subselection():
    @op(required_resource_keys={"foo"})
    def the_op(context):
        return context.resources.foo

    @op(required_resource_keys={"bar"})
    def other_op(context):
        return context.resources.bar

    @graph
    def the_graph():
        the_op()
        other_op()

    pending_job = the_graph.to_pending_job(
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("foo")}
    )
    pending_job = pending_job.get_job_def_for_op_selection(["other_op"])
    job_def = pending_job.coerce_to_job_def(
        resource_defs={
            "bar": ResourceDefinition.hardcoded_resource("bar"),
            "foo": ResourceDefinition.hardcoded_resource("baz"),
        }
    )
    result = job_def.execute_in_process()
    assert result.success
    assert len(result.events_for_node("the_op")) == 0
    assert len(result.events_for_node("other_op")) > 0
    assert result.output_for_node("other_op") == "bar"
