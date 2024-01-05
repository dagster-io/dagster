from ..defs import defs, my_job


def test_defs():
    # The job name corresponds to the name of the function defining the job.
    # In our example, the job is created from a graph,
    # which is defined by the function `my_graph()`,
    # therefore the name of the job is `my_graph`.
    test_job = defs.get_job_def("my_graph")
    assert test_job == my_job
    assert test_job.execute_in_process().output_for_node("my_op")
