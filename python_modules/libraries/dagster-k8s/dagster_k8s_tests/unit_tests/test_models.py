import kubernetes
import pytest
from dagster_k8s.models import k8s_model_from_dict


def test_deserialize_volume():
    volume_dict = {
        "name": "my_volume",
        "configMap": {
            "name": "my_config_map",
        },
    }

    model = k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)
    assert model.name == "my_volume"
    assert model.config_map.name == "my_config_map"


def test_bad_source_structure():
    volume_dict = {"name": "my_volume", "configMap": "my_config_map"}

    with pytest.raises(
        Exception,
        match="Attribute configMap of type V1ConfigMapVolumeSource must be a dict, received my_config_map instead",
    ):
        k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)


def test_extra_key():
    volume_dict = {
        "name": "my_volume",
        "configMap": {
            "name": "my_config_map",
        },
        "extraKey": "extra_val",
    }
    with pytest.raises(Exception, match="Unexpected keys in model class V1Volume: {'extraKey'}"):
        k8s_model_from_dict(kubernetes.client.V1Volume, volume_dict)
