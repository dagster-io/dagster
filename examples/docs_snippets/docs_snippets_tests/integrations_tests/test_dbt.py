import pytest
from docs_snippets.integrations.dbt import (
    scope_dbt_cli_config_exclude_models,
    scope_dbt_cli_config_executable,
    scope_dbt_cli_config_profile_and_target,
    scope_dbt_cli_config_select_models,
    scope_dbt_cli_config_vars,
    scope_dbt_cli_profile_modes,
    scope_dbt_cli_resource_config,
    scope_dbt_cli_run,
    scope_dbt_cli_run_after_another_solid,
    scope_dbt_cli_run_specific_models,
    scope_dbt_cli_run_specific_models_runtime,
    scope_dbt_rpc_and_wait_config_polling_interval,
    scope_dbt_rpc_config_disable_assets,
    scope_dbt_rpc_config_exclude_models,
    scope_dbt_rpc_config_select_models,
    scope_dbt_rpc_resource,
    scope_dbt_rpc_resource_example,
    scope_dbt_rpc_run,
    scope_dbt_rpc_run_and_wait,
    scope_dbt_rpc_run_specific_models,
)


@pytest.mark.parametrize(
    "scope",
    [
        scope_dbt_cli_resource_config,
        scope_dbt_cli_run,
        scope_dbt_cli_run_specific_models,
        scope_dbt_cli_run_specific_models_runtime,
        scope_dbt_cli_profile_modes,
        scope_dbt_cli_run_after_another_solid,
        scope_dbt_rpc_resource,
        scope_dbt_rpc_run,
        scope_dbt_rpc_run_specific_models,
        scope_dbt_rpc_run_and_wait,
        scope_dbt_cli_config_profile_and_target,
        scope_dbt_cli_config_executable,
        scope_dbt_cli_config_select_models,
        scope_dbt_cli_config_exclude_models,
        scope_dbt_cli_config_vars,
        scope_dbt_rpc_resource_example,
        scope_dbt_rpc_config_select_models,
        scope_dbt_rpc_config_exclude_models,
        scope_dbt_rpc_and_wait_config_polling_interval,
        scope_dbt_rpc_config_disable_assets,
    ],
)
def test_valid_scope(scope):
    # test that the scope has valid syntax
    scope()
