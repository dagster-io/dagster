import datetime
import re
from collections.abc import Mapping
from typing import Any, TypeVar

import dagster._check as check
import kubernetes
import kubernetes.client.models
from dagster._vendored.dateutil.parser import parse
from kubernetes.client.api_client import ApiClient
from kubernetes.client.configuration import Configuration

# Unclear what the correct type is to use for a bound here.
T_KubernetesModel = TypeVar("T_KubernetesModel")


# Create a single Configuration object to pass through to each model creation -
# the default otherwise in the OpenAPI version currently in use by the k8s
# client will create one on each model creation otherwise, which can cause
# lock contention since it acquires the global python logger lock
# see: https://github.com/kubernetes-client/python/issues/1921
shared_k8s_model_configuration = Configuration()


def _get_k8s_class(classname: str) -> type[Any]:
    if classname in ApiClient.NATIVE_TYPES_MAPPING:
        return ApiClient.NATIVE_TYPES_MAPPING[classname]
    else:
        return getattr(kubernetes.client.models, classname)


def _is_openapi_list_type(attr_type: str) -> bool:
    return attr_type.startswith("list[")


def _get_openapi_list_element_type(attr_type: str) -> str:
    match = check.not_none(re.match(r"list\[(.*)\]", attr_type))
    return match.group(1)


def _is_openapi_dict_type(attr_type: str) -> bool:
    return attr_type.startswith("dict(")


def _get_openapi_dict_value_type(attr_type: str) -> str:
    # group(2) because value, not key
    match = check.not_none(re.match(r"dict\(([^,]*), (.*)\)", attr_type))
    return match.group(2)


def _k8s_parse_value(data: Any, classname: str, attr_name: str) -> Any:
    if data is None:
        return None

    if _is_openapi_list_type(classname):
        sub_kls = _get_openapi_list_element_type(classname)
        return [
            _k8s_parse_value(value, sub_kls, f"{attr_name}[{index}]")
            for index, value in enumerate(data)
        ]

    if _is_openapi_dict_type(classname):
        sub_kls = _get_openapi_dict_value_type(classname)
        return {k: _k8s_parse_value(v, sub_kls, f"{attr_name}[{k}]") for k, v in data.items()}

    klass = _get_k8s_class(classname)

    if klass in ApiClient.PRIMITIVE_TYPES:
        return klass(data)
    elif klass == object:
        return data
    elif klass == datetime.date:
        return parse(data).date()  # pyright: ignore[reportAttributeAccessIssue]
    elif klass == datetime.datetime:
        return parse(data)
    else:
        if not isinstance(data, dict):
            raise Exception(
                f"Attribute {attr_name} of type {klass.__name__} must be a dict, received"
                f" {data} instead"
            )

        return k8s_model_from_dict(klass, data)


def _k8s_snake_case_value(val: Any, attr_type: str, attr_name: str) -> Any:
    if _is_openapi_list_type(attr_type):
        sub_kls = _get_openapi_list_element_type(attr_type)
        return [
            _k8s_snake_case_value(list_value, sub_kls, f"{attr_name}[{index}]")
            for index, list_value in enumerate(val)
        ]
    elif _is_openapi_dict_type(attr_type):
        sub_kls = _get_openapi_dict_value_type(attr_type)
        return {k: _k8s_snake_case_value(v, sub_kls, f"{attr_name}[{k}]") for k, v in val.items()}
    else:
        klass = _get_k8s_class(attr_type)
        if klass in ApiClient.PRIMITIVE_TYPES or klass in (
            object,
            datetime.date,
            datetime.datetime,
        ):
            return val
        else:
            if not isinstance(val, dict):
                raise Exception(
                    f"Attribute {attr_name} of type {klass.__name__} must be a dict, received"
                    f" {val} instead"
                )
            return k8s_snake_case_dict(klass, val)


def k8s_snake_case_keys(model_class, model_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    snake_case_to_camel_case = model_class.attribute_map
    camel_case_to_snake_case = dict((v, k) for k, v in snake_case_to_camel_case.items())

    snake_case_dict = {}
    for key, val in model_dict.items():
        snake_case_key = camel_case_to_snake_case[key] if key in camel_case_to_snake_case else key

        if snake_case_key != key and snake_case_key in model_dict:
            raise Exception(
                f"Model class {model_class.__name__} cannot contain both {key} and"
                f" {snake_case_key} keys"
            )

        snake_case_dict[snake_case_key] = val

    invalid_keys = set(snake_case_dict).difference(snake_case_to_camel_case)

    if len(invalid_keys):
        raise Exception(f"Unexpected keys in model class {model_class.__name__}: {invalid_keys}")

    return snake_case_dict


def k8s_snake_case_dict(model_class: type[Any], model_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    snake_case_dict = k8s_snake_case_keys(model_class, model_dict)

    final_dict = {}
    for key, val in snake_case_dict.items():
        attr_type = model_class.openapi_types[key]
        final_dict[key] = _k8s_snake_case_value(val, attr_type, key)

    return final_dict


# Heavily inspired by kubernetes.client.ApiClient.__deserialize_model, with more validation
# that the keys and values match the expected format. Requires k8s attribute names to be in
# snake_case.
def k8s_model_from_dict(
    model_class: type[T_KubernetesModel], model_dict: Mapping[str, Any]
) -> T_KubernetesModel:
    check.mapping_param(model_dict, "model_dict")

    expected_keys = set(model_class.attribute_map.keys())  # type: ignore
    invalid_keys = set(model_dict).difference(expected_keys)

    if len(invalid_keys):
        raise Exception(f"Unexpected keys in model class {model_class.__name__}: {invalid_keys}")

    # Pass through the configuration object since the default implementation creates a new one
    # in the constructor, which can create lock contention if multiple threads are calling this
    # simultaneously
    kwargs = {"local_vars_configuration": shared_k8s_model_configuration}
    for attr, attr_type in model_class.openapi_types.items():  # type: ignore
        # e.g. config_map => configMap
        if attr in model_dict:
            value = model_dict[attr]
            kwargs[attr] = _k8s_parse_value(value, attr_type, attr)

    return model_class(**kwargs)
