from ..connecting_ops.complex_job import diamond, get_total_size


# start_op_test
def test_get_total_size():
    file_sizes = {"file1": 400, "file2": 50}
    result = get_total_size(file_sizes)
    assert result == 450


# end_op_test

# start_job_test
def test_diamond():
    res = diamond.execute_in_process()
    assert res.success
    assert res.output_for_node("get_total_size") > 0


# end_job_test
