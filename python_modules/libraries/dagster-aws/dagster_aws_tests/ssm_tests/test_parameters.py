import boto3
from moto import mock_ssm
from pytest import fixture

from dagster_aws.ssm.parameters import get_parameters_by_tags, get_parameters_by_paths
from dagster_aws.ssm import parameter_store_resource


@fixture
def mock_ssm_client_resource():
    with mock_ssm():
        yield boto3.client("ssm")


def test_get_parameters_from_tags(mock_ssm_client_resource):
    mock_ssm_client_resource.put_parameter(Name="foo_param1", Value="foo_value1", Tags=[{"Key": "foo_tag_key",
                                                                                       "Value": "foo_tag_value1"}])
    mock_ssm_client_resource.put_parameter(Name="foo_param2", Value="foo_value2", Tags=[{"Key": "foo_tag_key",
                                                                                         "Value": "foo_tag_value2"}])
    mock_ssm_client_resource.put_parameter(Name="bar_param", Value="bar_value", Tags=[{"Key": "bar_tag_key",
                                                                                       "Value": "bar_tag_value"}])
    result = get_parameters_by_tags(mock_ssm_client_resource, parameter_tags=[{"key": "foo_tag_key",
                                                                              "values": ["foo_tag_value1",
                                                                                         "foo_tag_value2"]}],
                                    with_decryption=False)
    assert result == {"foo_param1": "foo_value1",
                      "foo_param2": "foo_value2"}

    result = get_parameters_by_tags(mock_ssm_client_resource, parameter_tags=[{"key": "non-existent",
                                                                              "values": ["non-existent"]}], with_decryption=False)
    assert result == {}


def test_get_parameters_by_path(mock_ssm_client_resource):
    mock_ssm_client_resource.put_parameter(Name="path/based/param1", Value="param1")
    mock_ssm_client_resource.put_parameter(Name="path/based/nested/param2", Value="param2")
    mock_ssm_client_resource.put_parameter(Name="path/not/matching/param3", Value="param3")

    result = get_parameters_by_paths(mock_ssm_client_resource, ["path/based"], with_decryption=True, recursive=True)
    assert result == {'path/based/param1': 'param1', 'path/based/nested/param2': 'param2'}

    result = get_parameters_by_paths(mock_ssm_client_resource, ["path/based"], with_decryption=True, recursive=False)
    assert result == {"path/based/param1": "param1"}

    result = get_parameters_by_paths(mock_ssm_client_resource, ["path/"], with_decryption=False, recursive=False)
    assert result == {}
