from dagster_aws.ssm.parameters import get_parameters_by_paths, get_parameters_by_tags


def test_get_parameters_from_tags(mock_ssm_client):
    mock_ssm_client.put_parameter(
        Name="foo_param1",
        Type="String",
        Value="foo_value1",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value1"}],
    )
    mock_ssm_client.put_parameter(
        Name="foo_param2",
        Type="String",
        Value="foo_value2",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value2"}],
    )
    mock_ssm_client.put_parameter(
        Name="bar_param",
        Type="String",
        Value="bar_value",
        Tags=[{"Key": "bar_tag_key", "Value": "bar_tag_value"}],
    )
    result = get_parameters_by_tags(
        mock_ssm_client,
        parameter_tags=[{"key": "foo_tag_key", "values": ["foo_tag_value1", "foo_tag_value2"]}],
        with_decryption=False,
    )
    assert result == {"foo_param1": "foo_value1", "foo_param2": "foo_value2"}

    result = get_parameters_by_tags(
        mock_ssm_client,
        parameter_tags=[{"key": "non-existent", "values": ["non-existent"]}],
        with_decryption=False,
    )
    assert result == {}


def test_get_parameters_by_path(mock_ssm_client):
    mock_ssm_client.put_parameter(Name="path/based/param1", Value="param1", Type="String")
    mock_ssm_client.put_parameter(Name="path/based/nested/param2", Value="param2", Type="String")
    mock_ssm_client.put_parameter(Name="path/not/matching/param3", Value="param3", Type="String")

    result = get_parameters_by_paths(
        mock_ssm_client, ["path/based"], with_decryption=True, recursive=True
    )
    assert result == {"path/based/param1": "param1", "path/based/nested/param2": "param2"}

    result = get_parameters_by_paths(
        mock_ssm_client, ["path/based"], with_decryption=True, recursive=False
    )
    assert result == {"path/based/param1": "param1"}

    result = get_parameters_by_paths(
        mock_ssm_client, ["path/"], with_decryption=False, recursive=False
    )
    assert result == {}
