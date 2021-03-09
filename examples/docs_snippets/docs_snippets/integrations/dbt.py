# pylint: disable=unused-variable


def scope_dbt_cli_run():
    # start_marker_dbt_cli_run
    from dagster import pipeline
    from dagster_dbt import dbt_cli_run

    config = {"project-dir": "path/to/dbt/project"}
    run_all_models = dbt_cli_run.configured(config, name="run_dbt_project")

    @pipeline
    def my_dbt_pipeline():
        run_all_models()

    # end_marker_dbt_cli_run


def scope_dbt_cli_run_specific_models():
    # start_marker_dbt_cli_run_specific_models
    from dagster import pipeline
    from dagster_dbt import dbt_cli_run

    config = {"project-dir": "path/to/dbt/project", "models": ["tag:staging"]}
    run_staging_models = dbt_cli_run.configured(config, name="run_staging_models")

    @pipeline
    def my_dbt_pipeline():
        run_staging_models()

    # end_marker_dbt_cli_run_specific_models


def scope_dbt_rpc_resource():
    # start_marker_dbt_rpc_resource
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})
    # end_marker_dbt_rpc_resource


def scope_dbt_rpc_run():
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})

    # start_marker_dbt_rpc_run
    from dagster import ModeDefinition, pipeline
    from dagster_dbt import dbt_rpc_run

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt_rpc": my_remote_rpc})])
    def my_dbt_pipeline():
        dbt_rpc_run()

    # end_marker_dbt_rpc_run


def scope_dbt_rpc_run_specific_models():
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})
    # start_marker_dbt_rpc_run_specific_models
    from dagster import ModeDefinition, pipeline
    from dagster_dbt import dbt_rpc_run

    run_staging_models = dbt_rpc_run.configured(
        {"models": ["tag:staging"]},
        name="run_staging_models",
    )

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt_rpc": my_remote_rpc})])
    def my_dbt_pipeline():
        run_staging_models()

    # end_marker_dbt_rpc_run_specific_models


def scope_dbt_rpc_run_and_wait():
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})
    # start_marker_dbt_rpc_run_and_wait
    from dagster import ModeDefinition, pipeline
    from dagster_dbt import dbt_rpc_run_and_wait

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt_rpc": my_remote_rpc})])
    def my_dbt_pipeline():
        dbt_rpc_run_and_wait()

    # end_marker_dbt_rpc_run_and_wait


def scope_dbt_cli_config_profile_and_target():
    PROFILE_NAME, TARGET_NAME = "", ""

    # start_marker_dbt_cli_config_profile_and_target
    config = {"profile": PROFILE_NAME, "target": TARGET_NAME}

    from dagster_dbt import dbt_cli_run

    custom_solid = dbt_cli_run.configured(config, name="custom_solid")
    # end_marker_dbt_cli_config_profile_and_target


def scope_dbt_cli_config_executable():
    # start_marker_dbt_cli_config_executable
    config = {"dbt_executable": "path/to/dbt/executable"}

    from dagster_dbt import dbt_cli_run

    custom_solid = dbt_cli_run.configured(config, name="custom_solid")
    # end_marker_dbt_cli_config_executable


def scope_dbt_cli_config_select_models():
    # start_marker_dbt_cli_config_select_models
    config = {"models": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    from dagster_dbt import dbt_cli_run

    custom_solid = dbt_cli_run.configured(config, name="custom_solid")
    # end_marker_dbt_cli_config_select_models


def scope_dbt_cli_config_exclude_models():
    # start_marker_dbt_cli_config_exclude_models
    config = {"exclude": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    from dagster_dbt import dbt_cli_run

    custom_solid = dbt_cli_run.configured(config, name="custom_solid")
    # end_marker_dbt_cli_config_exclude_models


def scope_dbt_cli_config_vars():
    # start_marker_dbt_cli_config_vars
    config = {"vars": {"key": "value"}}

    from dagster_dbt import dbt_cli_run

    custom_solid = dbt_cli_run.configured(config, name="custom_solid")
    # end_marker_dbt_cli_config_vars


def scope_dbt_cli_config_disable_assets():
    # start_marker_dbt_cli_config_disable_assets
    config = {"yield_materializations": False}

    from dagster_dbt import dbt_cli_run

    custom_solid = dbt_cli_run.configured(config, name="custom_solid")
    # end_marker_dbt_cli_config_disable_assets


def scope_dbt_rpc_resource_example():
    HOST, PORT = "", ""
    # start_marker_dbt_rpc_resource_example
    from dagster_dbt import dbt_rpc_resource

    custom_resource = dbt_rpc_resource.configured({"host": HOST, "post": PORT})
    # end_marker_dbt_rpc_resource_example


def scope_dbt_rpc_config_select_models():
    # start_marker_dbt_rpc_config_select_models
    config = {"models": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    from dagster_dbt import dbt_rpc_run

    custom_solid = dbt_rpc_run.configured(config, name="custom_solid")
    # end_marker_dbt_rpc_config_select_models


def scope_dbt_rpc_config_exclude_models():
    # start_marker_dbt_rpc_config_exclude_models
    config = {"exclude": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    from dagster_dbt import dbt_rpc_run

    custom_solid = dbt_rpc_run.configured(config, name="custom_solid")
    # end_marker_dbt_rpc_config_exclude_models


def scope_dbt_rpc_and_wait_config_polling_interval():
    # start_marker_dbt_rpc_and_wait_config_polling_interval
    config = {"interval": 3}  # Poll the dbt RPC server every 3 seconds.

    from dagster_dbt import dbt_rpc_run

    custom_solid = dbt_rpc_run.configured(config, name="custom_solid")
    # end_marker_dbt_rpc_and_wait_config_polling_interval


def scope_dbt_rpc_config_disable_assets():
    # start_marker_dbt_rpc_config_disable_assets
    config = {"yield_materializations": False}

    from dagster_dbt import dbt_rpc_run

    custom_solid = dbt_rpc_run.configured(config, name="custom_solid")
    # end_marker_dbt_rpc_config_disable_assets
