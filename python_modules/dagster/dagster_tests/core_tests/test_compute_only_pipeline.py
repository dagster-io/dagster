from dagster import execute_pipeline, pipeline, solid


def _set_key_value(ddict, key, value):
    ddict[key] = value
    return value


def test_execute_solid_with_dep_only_inputs_no_api():
    did_run_dict = {}

    @solid
    def step_one_solid(_):
        _set_key_value(did_run_dict, "step_one", True)

    @solid
    def step_two_solid(_, _in):
        _set_key_value(did_run_dict, "step_two", True)

    @pipeline
    def pipe():
        step_two_solid(step_one_solid())

    pipeline_result = execute_pipeline(pipe)

    assert pipeline_result.success

    for result in pipeline_result.solid_result_list:
        assert result.success

    assert did_run_dict["step_one"] is True
    assert did_run_dict["step_two"] is True


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    @solid
    def step_one_solid(_):
        _set_key_value(did_run_dict, "step_one", True)

    @solid
    def step_two_solid(_, _in):
        _set_key_value(did_run_dict, "step_two", True)

    @pipeline
    def pipe():
        step_two_solid(step_one_solid())

    pipeline_result = execute_pipeline(pipe)

    for result in pipeline_result.solid_result_list:
        assert result.success

    assert did_run_dict["step_one"] is True
    assert did_run_dict["step_two"] is True
