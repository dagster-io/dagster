from ..defs import defs, my_job


def test_defs():
    test_job = defs.get_job_def("my_job")
    assert test_job == my_job
    assert test_job.execute_in_process().output_for_node("my_op")
