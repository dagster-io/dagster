from dagster import OutputDefinition


def test_output_definition():
    output_definiton_onlyreq = OutputDefinition(dagster_type=int, name="result", is_required=True)
    assert output_definiton_onlyreq.optional is False

    output_definiton_none = OutputDefinition(dagster_type=int, name="result")
    assert output_definiton_none.optional is False


def test_manager_key_default_value():
    output_def = OutputDefinition(manager_key=None)
    assert output_def.manager_key == "io_manager"
