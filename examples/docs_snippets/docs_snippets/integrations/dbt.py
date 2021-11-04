# pylint: disable=unused-variable


def scope_dbt_asset_mats():
    # start_marker_dbt_asset_mats
    from dagster import op, Output
    from dagster_dbt.utils import generate_materializations

    @op(required_resource_keys={"dbt"})
    def dbt_run_with_custom_assets(context):
        dbt_result = context.resources.dbt.run()
        for materialization in generate_materializations(dbt_result):
            yield materialization._replace(
                metadata_entries=[...]  # insert whatever metadata you want here
            )
        yield Output(dbt_result)

    # end_marker_dbt_asset_mats


def scope_dbt_cli_resource_config():
    # start_marker_dbt_cli_resource_config
    from dagster_dbt import dbt_cli_resource

    my_dbt_resource = dbt_cli_resource.configured(
        {"project_dir": "path/to/dbt/project", "profiles_dir": "path/to/dbt/profiles",}
    )
    # end_marker_dbt_cli_resource_config


def scope_dbt_cli_run():
    # start_marker_dbt_cli_run_preconfig
    from dagster import job
    from dagster_dbt import dbt_cli_resource, dbt_run_op

    my_dbt_resource = dbt_cli_resource.configured({"project_dir": "path/to/dbt/project"})

    @job(resource_defs={"dbt": my_dbt_resource})
    def my_dbt_job():
        dbt_run_op()

    # end_marker_dbt_cli_run_preconfig


def scope_dbt_cli_run_specific_models():
    # start_marker_dbt_cli_run_specific_models_preconfig
    from dagster import job
    from dagster_dbt import dbt_cli_resource, dbt_run_op

    my_dbt_resource = dbt_cli_resource.configured(
        {"project_dir": "path/to/dbt/project", "models": ["tag:staging"]}
    )

    @job(resource_defs={"dbt": my_dbt_resource})
    def my_dbt_job():
        dbt_run_op()

    # end_marker_dbt_cli_run_specific_models_preconfig


def scope_dbt_cli_run_specific_models_runtime():
    # start_marker_dbt_cli_run_specific_models_runtime
    from dagster import op

    @op(required_resource_keys={"dbt"})
    def run_models(context, some_condition: bool):
        if some_condition:
            context.resources.dbt.run(models=["tag:staging"])
        else:
            context.resources.dbt.run(models=["tag:other"])

    # end_marker_dbt_cli_run_specific_models_runtime


def scope_dbt_cli_profile_modes():
    # start_marker_dbt_cli_profile_modes
    from dagster import graph
    from dagster_dbt import dbt_cli_resource, dbt_run_op

    @graph
    def my_dbt():
        dbt_run_op()

    my_dbt_graph_dev = my_dbt.to_job(
        resource_defs={
            "dbt": dbt_cli_resource.configured(
                {"project_dir": "path/to/dbt/project", "profile": "dev"}
            )
        }
    )

    my_dbt_graph_prod = my_dbt.to_job(
        resource_defs={
            "dbt": dbt_cli_resource.configured(
                {"project_dir": "path/to/dbt/project", "profile": "prod"}
            )
        }
    )

    # end_marker_dbt_cli_profile_modes


def scope_dbt_cli_run_after_another_op():
    # start_marker_dbt_cli_run_after_another_op
    from dagster import job
    from dagster_dbt import dbt_cli_resource, dbt_run_op, dbt_test_op

    my_dbt_resource = dbt_cli_resource.configured({"project_dir": "path/to/dbt/project"})

    @job(resource_defs={"dbt": my_dbt_resource})
    def my_dbt_job():
        dbt_test_op(start_after=dbt_run_op())

    # end_marker_dbt_cli_run_after_another_op


def scope_dbt_rpc_resource():
    # start_marker_dbt_rpc_resource
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})
    # end_marker_dbt_rpc_resource


def scope_dbt_rpc_run():
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})

    # start_marker_dbt_rpc_run
    from dagster import job
    from dagster_dbt import dbt_run_op

    @job(resource_defs={"dbt": my_remote_rpc})
    def my_dbt_job():
        dbt_run_op()

    # end_marker_dbt_rpc_run


def scope_dbt_rpc_run_specific_models():

    # start_marker_dbt_rpc_run_specific_models
    from dagster import job, op
    from dagster_dbt import dbt_rpc_resource

    my_remote_rpc = dbt_rpc_resource.configured({"host": "80.80.80.80", "port": 8080})

    @op(required_resource_keys={"dbt"})
    def run_staging_models(context):
        context.resources.dbt.run(models=["tag:staging"])

    @job(resource_defs={"dbt": my_remote_rpc})
    def my_dbt_job():
        run_staging_models()

    # end_marker_dbt_rpc_run_specific_models


def scope_dbt_rpc_run_and_wait():
    # start_marker_dbt_rpc_run_and_wait
    from dagster import job, op
    from dagster_dbt import dbt_rpc_sync_resource

    my_remote_sync_rpc = dbt_rpc_sync_resource.configured({"host": "80.80.80.80", "port": 8080})

    @op(required_resource_keys={"dbt_sync"})
    def run_staging_models_and_wait(context):
        context.resources.dbt.run(models=["tag:staging"])

    @job(resource_defs={"dbt_sync": my_remote_sync_rpc})
    def my_dbt_job():
        run_staging_models_and_wait()

    # end_marker_dbt_rpc_run_and_wait


def scope_dbt_cli_config_profile_and_target():
    PROFILE_NAME, TARGET_NAME = "", ""

    # start_marker_dbt_cli_config_profile_and_target
    from dagster import job
    from dagster_dbt import dbt_cli_resource

    config = {"profile": PROFILE_NAME, "target": TARGET_NAME}

    @job(resource_defs={"dbt": dbt_cli_resource.configured(config)})
    def my_job():
        # ...
        # end_marker_dbt_cli_config_profile_and_target
        pass


def scope_dbt_cli_config_executable():
    # start_marker_dbt_cli_config_executable
    from dagster import job
    from dagster_dbt import dbt_cli_resource

    config = {"dbt_executable": "path/to/dbt/executable"}

    @job(resource_defs={"dbt": dbt_cli_resource.configured(config)})
    def my_job():
        # ...
        # end_marker_dbt_cli_config_executable
        pass


def scope_dbt_cli_config_select_models():
    # start_marker_dbt_cli_config_select_models
    from dagster import job
    from dagster_dbt import dbt_cli_resource

    config = {"models": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    @job(resource_defs={"dbt": dbt_cli_resource.configured(config)})
    def my_job():
        # ...
        # end_marker_dbt_cli_config_select_models
        pass


def scope_dbt_cli_config_exclude_models():
    # start_marker_dbt_cli_config_exclude_models
    from dagster import job
    from dagster_dbt import dbt_cli_resource

    config = {"exclude": ["my_dbt_model+", "path.to.models", "tag:nightly"]}

    @job(resource_defs={"dbt": dbt_cli_resource.configured(config)})
    def my_job():
        # ...
        # end_marker_dbt_cli_config_exclude_models
        pass


def scope_dbt_cli_config_vars():
    # start_marker_dbt_cli_config_vars
    from dagster import job
    from dagster_dbt import dbt_cli_resource

    config = {"vars": {"key": "value"}}

    @job(resource_defs={"dbt": dbt_cli_resource.configured(config)})
    def my_job():
        # ...
        # end_marker_dbt_cli_config_vars
        pass


def scope_dbt_rpc_resource_example():
    HOST, PORT = "", ""
    # start_marker_dbt_rpc_resource_example
    from dagster_dbt import dbt_rpc_resource

    custom_resource = dbt_rpc_resource.configured({"host": HOST, "post": PORT})
    # end_marker_dbt_rpc_resource_example


def scope_dbt_run_disable_assets():
    # start_marker_dbt_rpc_config_disable_assets
    from dagster import job
    from dagster_dbt import dbt_run_op, dbt_cli_resource

    dbt_run_no_assets = dbt_run_op.configured(
        {"yield_materializations": False}, name="dbt_run_no_assets"
    )

    @job(resource_defs={"dbt": dbt_cli_resource})
    def my_job():
        dbt_run_no_assets()
