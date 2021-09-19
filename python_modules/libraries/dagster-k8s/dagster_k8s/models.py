import datetime
from typing import Any, Dict

import kubernetes
from dagster import check
from dagster.utils import frozendict
from dateutil.parser import parse
from kubernetes.client import ApiClient


def _k8s_value(data, classname, attr_name):
    if classname in ApiClient.NATIVE_TYPES_MAPPING:
        klass = ApiClient.NATIVE_TYPES_MAPPING[classname]
    else:
        klass = getattr(kubernetes.client.models, classname)

    if klass in ApiClient.PRIMITIVE_TYPES:
        return klass(data)
    elif klass == object:
        return data
    elif klass == datetime.date:
        return parse(data).date()
    elif klass == datetime.datetime:
        return parse(data)
    else:
        if not isinstance(data, (frozendict, dict)):
            raise Exception(
                f"Attribute {attr_name} of type {klass.__name__} must be a dict, received {data} instead"
            )

        return k8s_model_from_dict(klass, data)


# Heavily inspired by kubernetes.client.ApiClient.__deserialize_model, but keys are in
# the with_underscores format already expected by Kubernetes python model
# objects (rather than the camelCase format of the kubernetes API)
def k8s_model_from_dict(model_class, model_dict: Dict[str, Any]):
    check.dict_param(model_dict, "model_dict")
    kwargs = {}

    expected_keys = set(model_class.openapi_types)
    invalid_keys = set(model_dict).difference(expected_keys)

    if len(invalid_keys):
        raise Exception(f"Unexpected keys in model class {model_class.__name__}: {invalid_keys}")

    for attr, attr_classname in model_class.openapi_types.items():
        if attr in model_dict:
            value = model_dict[attr]
            kwargs[attr] = _k8s_value(value, attr_classname, attr)

    return model_class(**kwargs)
