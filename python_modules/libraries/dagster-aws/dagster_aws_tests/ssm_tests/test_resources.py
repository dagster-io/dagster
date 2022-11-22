import os

from dagster_aws.ssm import parameter_store_resource

from dagster import build_init_resource_context
from dagster._core.test_utils import environ


def test_parameter_store_resource(mock_ssm_client):
    mock_ssm_client.put_parameter(
        Name="foo_param1",
        Value="foo_value1",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value1"}],
    )
    mock_ssm_client.put_parameter(
        Name="foo_param2",
        Value="foo_value2",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value2"}],
    )
    mock_ssm_client.put_parameter(
        Name="bar_param", Value="bar_value", Tags=[{"Key": "bar_tag_key", "Value": "bar_tag_value"}]
    )
    mock_ssm_client.put_parameter(
        Name="path/based/param1",
        Value="path_param1",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value3"}],
    )
    mock_ssm_client.put_parameter(
        Name="path/based/param1/nested",
        Value="path_param2",
    )
    mock_ssm_client.put_parameter(Name="other/path/param3", Value="param_param3")
    with parameter_store_resource(
        build_init_resource_context(config={"parameters": ["foo_param1", "foo_param2"]})
    ) as param_map:
        assert param_map == {"foo_param1": "foo_value1", "foo_param2": "foo_value2"}

    with parameter_store_resource(
        build_init_resource_context(config={"parameter_paths": ["path/based", "other/path"]})
    ) as param_map:
        assert param_map == {
            "path/based/param1": "path_param1",
            "path/based/param1/nested": "path_param2",
            "other/path/param3": "param_param3",
        }

    with parameter_store_resource(
        build_init_resource_context(
            config={
                "parameter_tags": [
                    {"key": "foo_tag_key", "values": ["foo_tag_value1", "foo_tag_value2"]}
                ]
            }
        )
    ) as param_map:
        assert param_map == {"foo_param1": "foo_value1", "foo_param2": "foo_value2"}

    with parameter_store_resource(
        build_init_resource_context(
            config={
                "parameters": ["foo_param1"],
                "parameter_paths": ["path/based"],
                "parameter_tags": [{"key": "foo_tag_key", "values": ["foo_tag_value2"]}],
            }
        )
    ) as param_map:
        assert param_map == {
            "foo_param1": "foo_value1",
            "foo_param2": "foo_value2",
            "path/based/param1": "path_param1",
            "path/based/param1/nested": "path_param2",
        }


def test_parameters_added_to_environment(mock_ssm_client):
    mock_ssm_client.put_parameter(
        Name="foo_param1",
        Value="foo_value1",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value1"}],
    )
    mock_ssm_client.put_parameter(
        Name="foo_param2",
        Value="foo_value2",
        Tags=[{"Key": "foo_tag_key", "Value": "foo_tag_value2"}],
    )

    assert os.getenv("foo_param1") is None
    assert os.getenv("foo_param2") is None

    with parameter_store_resource(
        build_init_resource_context(
            config={"parameters": ["foo_param1"], "add_to_environment": True}
        )
    ) as param_map:
        assert param_map == {"foo_param1": "foo_value1"}
        assert os.getenv("foo_param1") == "foo_value1"

    with environ({"foo_param2": "prior_foo2_value"}):
        assert os.getenv("foo_param2") == "prior_foo2_value"

        with parameter_store_resource(
            build_init_resource_context(
                config={"parameters": ["foo_param2"], "add_to_environment": True}
            )
        ) as param_map:
            assert param_map == {"foo_param2": "foo_value2"}
            assert os.getenv("foo_param2") == "foo_value2"
