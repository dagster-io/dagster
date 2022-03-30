import re

import kubernetes
import pytest
from dagster_k8s.models import k8s_model_from_dict, k8s_snake_case_dict


def test_deserialize_volume():
    volume_dict = {
        "name": "my_volume",
        "config_map": {
            "name": "my_config_map",
        },
    }

    model = k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)
    assert model.name == "my_volume"
    assert model.config_map.name == "my_config_map"


def test_bad_source_structure():
    volume_dict = {"name": "my_volume", "config_map": "my_config_map"}

    with pytest.raises(
        Exception,
        match="Attribute config_map of type V1ConfigMapVolumeSource must be a dict, received my_config_map instead",
    ):
        k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)


def test_extra_key():
    volume_dict = {
        "name": "my_volume",
        "config_map": {
            "name": "my_config_map",
        },
        "extra_key": "extra_val",
    }
    with pytest.raises(Exception, match="Unexpected keys in model class V1Volume: {'extra_key'}"):
        k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)


def test_list_type():
    volume_dict = {
        "name": "my_volume",
        "cephfs": {
            "monitors": [
                "ip1",
                "ip2",
            ],
            "path": "my_path",
            "secret_ref": {"name": "my_secret"},
            "user": "my_user",
        },
    }
    model = k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)
    assert model.cephfs.monitors == ["ip1", "ip2"]


def test_incorrect_list_value_type():
    volume_dict = {
        "name": "my_volume",
        "config_map": {
            "items": [{"key": "my_key", "path": "my_path"}, "foobar"],
        },
    }
    with pytest.raises(
        Exception,
        match=re.escape(
            "Attribute items[1] of type V1KeyToPath must be a dict, received foobar instead"
        ),
    ):
        k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)


def test_dict_type():
    volume_dict = {
        "name": "my_volume",
        "csi": {
            "driver": "my_driver",
            "volume_attributes": {"foo_key": "foo_val", "bar_key": "bar_val"},
        },
    }
    model = k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)
    assert model.csi.volume_attributes == {"foo_key": "foo_val", "bar_key": "bar_val"}


def test_snake_case_dict_type():
    volume_dict = {
        "name": "my_volume",
        "csi": {
            "driver": "my_driver",
            "volumeAttributes": {"fooKey": "fooVal", "bar_key": "barVal"},
        },
    }
    assert k8s_snake_case_dict(kubernetes.client.V1Volume, volume_dict) == {
        "name": "my_volume",
        "csi": {
            "driver": "my_driver",
            "volume_attributes": {"fooKey": "fooVal", "bar_key": "barVal"},
        },
    }


def test_snake_case_combined_with_camel_case():
    volume_dict = {
        "name": "my_volume",
        "csi": {
            "driver": "my_driver",
            "volumeAttributes": {"fooKey": "fooVal", "bar_key": "barVal"},
            "volume_attributes": {"fooKey": "fooVal", "bar_key": "barVal"},
        },
    }
    with pytest.raises(
        Exception,
        match="Model class V1CSIVolumeSource cannot contain both volumeAttributes and volume_attributes keys",
    ):
        k8s_snake_case_dict(kubernetes.client.V1Volume, volume_dict)


def test_snake_case_extra_key():
    volume_dict = {
        "name": "my_volume",
        "configMap": {
            "name": "my_config_map",
        },
        "extraKey": "extra_val",
    }
    with pytest.raises(Exception, match="Unexpected keys in model class V1Volume: {'extraKey'}"):
        k8s_snake_case_dict(kubernetes.client.V1Volume, volume_dict)
