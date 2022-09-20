from dagster import job, op


def _set_key_value(ddict, key, value):
    ddict[key] = value
    return value


def test_execute_solid_with_dep_only_inputs_no_api():
    did_run_dict = {}

    @op
    def step_one_op(_):
        _set_key_value(did_run_dict, "step_one", True)

    @op
    def step_two_op(_, _in):
        _set_key_value(did_run_dict, "step_two", True)

    @job
    def pipe():
        step_two_op(step_one_op())

    pipeline_result = pipe.execute_in_process()

    assert pipeline_result.success

    assert did_run_dict["step_one"] is True
    assert did_run_dict["step_two"] is True


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    @op
    def step_one_op(_):
        _set_key_value(did_run_dict, "step_one", True)

    @op
    def step_two_op(_, _in):
        _set_key_value(did_run_dict, "step_two", True)

    @job
    def pipe():
        step_two_op(step_one_op())

    pipeline_result = pipe.execute_in_process()

    assert did_run_dict["step_one"] is True
    assert did_run_dict["step_two"] is True
