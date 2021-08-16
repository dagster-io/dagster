# pylint: disable=unused-variable


def scope_dbt_cli_resource_config():
    # start_marker_dbt_cli_resource_config
    from dagster_dbt import dbt_cli_resource

    my_dbt_resource = dbt_cli_resource.configured(
        {"project_dir": "path/to/dbt/project", "profiles_dir": "path/to/dbt/profiles"}
    )
    # end_marker_dbt_cli_resource_config


def scope_dbt_cli_run():
    # start_marker_dbt_cli_run_preconfig
    from dagster import pipeline, solid, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    my_dbt_resource = dbt_cli_resource.configured({"project_dir": "path/to/dbt/project"})

    @solid(required_resource_keys={"dbt"})
    def run_all_models(context):
        context.resources.dbt.run()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt": my_dbt_resource})])
    def my_dbt_pipeline():
        run_all_models()

    # end_marker_dbt_cli_run_preconfig


def scope_dbt_cli_run_specific_models():
    # start_marker_dbt_cli_run_specific_models_preconfig
    from dagster import pipeline, solid, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    my_dbt_resource = dbt_cli_resource.configured(
        {"project_dir": "path/to/dbt/project", "models": ["tag:staging"]}
    )

    @solid(required_resource_keys={"dbt"})
    def run_models(context):
        context.resources.dbt.run()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt": my_dbt_resource})])
    def my_dbt_pipeline():
        run_models()

    # end_marker_dbt_cli_run_specific_models_preconfig


def scope_dbt_cli_run_specific_models_runtime():
    # start_marker_dbt_cli_run_specific_models_runtime
    from dagster import solid

    @solid(required_resource_keys={"dbt"})
    def run_models(context, some_condition: bool):
        if some_condition:
            context.resources.dbt.run(models=["tag:staging"])
        else:
            context.resources.dbt.run(models=["tag:other"])

    # end_marker_dbt_cli_run_specific_models_runtime


def scope_dbt_cli_profile_modes():
    # start_marker_dbt_cli_profile_modes
    from dagster import pipeline, solid, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    @solid(required_resource_keys={"dbt"})
    def run_all_models(context):
        context.resources.dbt.run()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                "dev",
                resource_defs={
                    "dbt": dbt_cli_resource.configured(
                        {"project_dir": "path/to/dbt/project", "profile": "dev"}
                    )
                },
            ),
            ModeDefinition(
                "prod",
                resource_defs={
                    "dbt": dbt_cli_resource.configured(
                        {"project_dir": "path/to/dbt/project", "profile": "prod"}
                    )
                },
            ),
        ]
    )
    def my_dbt_pipeline():
        run_all_models()

    # end_marker_dbt_cli_profile_modes


def scope_dbt_cli_run_after_another_solid():
    # start_marker_dbt_cli_run_after_another_solid
    from dagster import pipeline, solid, ModeDefinition
    from dagster_dbt import dbt_cli_resource, DbtCliOutput

    my_dbt_resource = dbt_cli_resource.configured({"project_dir": "path/to/dbt/project"})

    @solid(required_resource_keys={"dbt"})
    def run_models(context) -> DbtCliOutput:
        return context.resources.dbt.run()

    @solid(required_resource_keys={"dbt"})
    def test_models(context, run_result: DbtCliOutput):
        context.log.info(f"testing result of `{run_result.command}`!")
        context.resources.dbt.test()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt": my_dbt_resource})])
    def my_dbt_pipeline():
        run_result = run_models()
        test_models(run_result)

    # end_marker_dbt_cli_run_after_another_solid


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
    from dagster import pipeline, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    config = {"profile": PROFILE_NAME, "target": TARGET_NAME}

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"dbt": dbt_cli_resource.configured(config)})]
    )
    def my_pipeline():
        # ...
        # end_marker_dbt_cli_config_profile_and_target
        pass


def scope_dbt_cli_config_executable():
    # start_marker_dbt_cli_config_executable
    from dagster import pipeline, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    config = {"dbt_executable": "path/to/dbt/executable"}

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"dbt": dbt_cli_resource.configured(config)})]
    )
    def my_pipeline():
        # ...
        # end_marker_dbt_cli_config_executable
        pass


def scope_dbt_cli_config_select_models():
    # start_marker_dbt_cli_config_select_models
    from dagster import pipeline, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    config = {"models": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"dbt": dbt_cli_resource.configured(config)})]
    )
    def my_pipeline():
        # ...
        # end_marker_dbt_cli_config_select_models
        pass


def scope_dbt_cli_config_exclude_models():
    # start_marker_dbt_cli_config_exclude_models
    from dagster import pipeline, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    config = {"exclude": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"dbt": dbt_cli_resource.configured(config)})]
    )
    def my_pipeline():
        # ...
        # end_marker_dbt_cli_config_exclude_models
        pass


def scope_dbt_cli_config_vars():
    # start_marker_dbt_cli_config_vars
    from dagster import pipeline, ModeDefinition
    from dagster_dbt import dbt_cli_resource

    config = {"vars": {"key": "value"}}

    @pipeline(
        mode_defs=[ModeDefinition(resource_defs={"dbt": dbt_cli_resource.configured(config)})]
    )
    def my_pipeline():
        # ...
        # end_marker_dbt_cli_config_vars
        pass


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
