from dagster import OutputDefinition


def test_output_definition():
    output_definiton_onlyreq = OutputDefinition(dagster_type=int, name="result", is_required=True)
    assert output_definiton_onlyreq.optional is False

    output_definiton_none = OutputDefinition(dagster_type=int, name="result")
    assert output_definiton_none.optional is False


def test_asset_store_key_default_value():
    output_def = OutputDefinition(asset_store_key=None)
    assert output_def.asset_store_key == "asset_store"
