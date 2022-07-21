from dagster import In, OpDefinition, Out, Output, job


def test_op_def_direct():
    def the_op_fn(_, inputs):
        assert inputs["x"] == 5
        yield Output(inputs["x"] + 1, output_name="the_output")

    op_def = OpDefinition(
        the_op_fn, "the_op", ins={"x": In(dagster_type=int)}, outs={"the_output": Out(int)}
    )

    @job
    def the_job(x):
        op_def(x)

    result = the_job.execute_in_process(input_values={"x": 5})
    assert result.success
