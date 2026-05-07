import importlib
import inspect
import pkgutil
from functools import cache
from types import UnionType
from typing import Union, get_args, get_origin

import pytest
from dagster_rest_resources.api.agent import DgApiAgentApi
from dagster_rest_resources.api.alert_policy import DgApiAlertPolicyApi
from dagster_rest_resources.api.artifact import DgApiArtifactApi
from dagster_rest_resources.api.asset import DgApiAssetApi
from dagster_rest_resources.api.asset_check import DgApiAssetCheckApi
from dagster_rest_resources.api.code_location import DgApiCodeLocationApi
from dagster_rest_resources.api.compute_log import DgApiComputeLogApi
from dagster_rest_resources.api.deployment import DgApiDeploymentApi
from dagster_rest_resources.api.issue import DgApiIssueApi
from dagster_rest_resources.api.job import DgApiJobApi
from dagster_rest_resources.api.organization import DgApiOrganizationApi
from dagster_rest_resources.api.run import DgApiRunApi
from dagster_rest_resources.api.run_event import DgApiRunEventApi
from dagster_rest_resources.api.schedule import DgApiScheduleApi
from dagster_rest_resources.api.secret import DgApiSecretApi
from dagster_rest_resources.api.sensor import DgApiSensorApi
from dagster_rest_resources.api.tick import DgApiTickApi
from pydantic import BaseModel

ALL_API_CLASSES = [
    DgApiAgentApi,
    DgApiAlertPolicyApi,
    DgApiArtifactApi,
    DgApiAssetCheckApi,
    DgApiAssetApi,
    DgApiCodeLocationApi,
    DgApiComputeLogApi,
    DgApiDeploymentApi,
    DgApiIssueApi,
    DgApiJobApi,
    DgApiOrganizationApi,
    DgApiRunEventApi,
    DgApiRunApi,
    DgApiScheduleApi,
    DgApiSecretApi,
    DgApiSensorApi,
    DgApiTickApi,
]


class TestRestCompliance:
    """Test REST compliance for API interfaces."""

    @pytest.mark.parametrize("api_class", ALL_API_CLASSES)
    def test_method_naming_conventions(self, api_class):
        """Test that all public methods follow REST naming conventions."""
        public_method_names = [
            m for m in dir(api_class) if not m.startswith("_") and callable(getattr(api_class, m))
        ]

        for name in public_method_names:
            is_valid_prefix = any(name.startswith(prefix) for prefix in REST_PREFIXES.keys())
            assert is_valid_prefix, (
                f"{api_class.__name__}.{name} doesn't follow REST naming conventions. "
                f"Should start with one of: {', '.join(REST_PREFIXES.keys())}"
            )

    @pytest.mark.parametrize("api_class", ALL_API_CLASSES)
    def test_return_type_signatures(self, api_class):
        """Test that methods only return Pydantic models that follow consistent patterns."""
        public_method_names = [
            m for m in dir(api_class) if not m.startswith("_") and callable(getattr(api_class, m))
        ]

        for name in public_method_names:
            method = getattr(api_class, name)
            sig = inspect.signature(method)

            return_type = sig.return_annotation

            assert is_pydantic_model(return_type), (
                f"{api_class.__name__}.{name} return type {return_type} must be a Pydantic model."
            )

            if name.startswith("list_"):
                fields = return_type.model_fields
                assert "items" in fields, (
                    f"{api_class.__name__}.{name} return type {return_type.__name__} "
                    f"should have an 'items' field for list responses."
                )


# REST method prefixes and their meanings
REST_PREFIXES = {
    "list_": "GET collection",
    "get_": "GET single resource",
    "create_": "POST resource",
    "update_": "PUT/PATCH resource",
    "delete_": "DELETE resource",
    "action_": "POST custom action",
}


@cache
def get_pydantic_models_from_schemas():
    """Discover all Pydantic models from the schemas package."""
    models = set()
    schemas_module = importlib.import_module("dagster_rest_resources.schemas")

    for _, module_name, _ in pkgutil.iter_modules(schemas_module.__path__):
        full_module_name = f"dagster_rest_resources.schemas.{module_name}"
        module = importlib.import_module(full_module_name)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                models.add(name)

    return frozenset(models)  # Return frozenset for hashability with @cache


def is_pydantic_model(type_hint) -> bool:
    """Check if a type hint is a Pydantic BaseModel subclass."""
    # Handle string annotations (forward references)
    if isinstance(type_hint, str):
        return type_hint in get_pydantic_models_from_schemas()

    # Handle Optional types
    if get_origin(type_hint) in (Union, UnionType):
        args = get_args(type_hint)
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return is_pydantic_model(non_none_args[0])
        return False

    return inspect.isclass(type_hint) and issubclass(type_hint, BaseModel)
