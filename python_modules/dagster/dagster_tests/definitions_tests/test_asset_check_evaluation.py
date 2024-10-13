from dagster._serdes import deserialize_value


def test_backcompat():
    old_value = (
        '{"__class__": "AssetCheckEvaluation", "asset_key": {"__class__": "AssetKey", "path":'
        ' ["a"]}, "check_name": "foo", "metadata": {}, "severity": {"__enum__":'
        ' "AssetCheckSeverity.ERROR"}, "success": true, "target_materialization_data": null}'
    )
    v = deserialize_value(old_value)
    assert v.passed
