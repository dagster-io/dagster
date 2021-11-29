from ..repo import my_job


def test_repo():
    assert my_job.execute_in_process().output_for_node("my_op")
