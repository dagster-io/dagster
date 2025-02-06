import os
from collections.abc import Mapping
from typing import cast

import dagster._check as check
from dagster._config import (
    EvaluateValueResult,
    Field,
    IntSource,
    ScalarUnion,
    Selector,
    StringSource,
    process_config,
)
from dagster._config.field_utils import Permissive
from dagster._core.errors import DagsterInvalidConfigError
from dagster._utils.merger import merge_dicts


def process_workspace_config(
    workspace_config: Mapping[str, object],
) -> EvaluateValueResult[Mapping[str, object]]:
    workspace_config = check.mapping_param(workspace_config, "workspace_config")

    return process_config(WORKSPACE_CONFIG_SCHEMA, workspace_config)


def ensure_workspace_config(
    workspace_config: Mapping[str, object], yaml_path: str
) -> Mapping[str, object]:
    check.str_param(yaml_path, "yaml_path")
    check.mapping_param(workspace_config, "workspace_config", key_type=str)

    validation_result = process_workspace_config(workspace_config)
    if not validation_result.success:
        raise DagsterInvalidConfigError(
            f"Errors while loading workspace config from {os.path.abspath(yaml_path)}.",
            validation_result.errors,
            workspace_config,
        )
    return cast(dict[str, object], validation_result.value)


def _get_target_config() -> Mapping[str, ScalarUnion]:
    return {
        "python_file": ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                "relative_path": StringSource,
                "attribute": Field(StringSource, is_required=False),
                "location_name": Field(StringSource, is_required=False),
                "working_directory": Field(StringSource, is_required=False),
                "executable_path": Field(StringSource, is_required=False),
            },
        ),
        "python_module": ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                "module_name": StringSource,
                "attribute": Field(StringSource, is_required=False),
                "working_directory": Field(StringSource, is_required=False),
                "location_name": Field(StringSource, is_required=False),
                "executable_path": Field(StringSource, is_required=False),
            },
        ),
        "python_package": ScalarUnion(
            scalar_type=str,
            non_scalar_schema={
                "package_name": StringSource,
                "attribute": Field(StringSource, is_required=False),
                "working_directory": Field(StringSource, is_required=False),
                "location_name": Field(StringSource, is_required=False),
                "executable_path": Field(StringSource, is_required=False),
            },
        ),
    }


WORKSPACE_CONFIG_SCHEMA = {
    "load_from": Field(
        [
            Selector(
                merge_dicts(
                    _get_target_config(),
                    {
                        "grpc_server": {
                            "host": Field(StringSource, is_required=False),
                            "socket": Field(StringSource, is_required=False),
                            "port": Field(IntSource, is_required=False),
                            "location_name": Field(StringSource, is_required=False),
                            "ssl": Field(bool, is_required=False),
                            "additional_metadata": Field(Permissive(), is_required=False),
                        },
                    },
                )
            )
        ],
        is_required=False,
    ),
}
