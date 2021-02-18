from os import path

import pytest
from dagster import (
    ModeDefinition,
    PipelineDefinition,
    check,
    execute_pipeline,
    fs_io_manager,
    in_process_executor,
    multiprocess_executor,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.definitions.executor import executor
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.retries import Retries
from dagster.core.test_utils import instance_for_test


def assert_pipeline_runs_with_executor(executor_defs, execution_config):
    it = {}

    @solid
    def a_solid(_):
        it["ran"] = True

    pipeline_def = PipelineDefinition(
        name="testing_pipeline",
        solid_defs=[a_solid],
        mode_defs=[ModeDefinition(executor_defs=executor_defs)],
    )

    result = execute_pipeline(pipeline_def, {"execution": execution_config})
    assert result.success
    assert it["ran"]


@pytest.mark.xfail(raises=check.ParameterCheckError)
def test_in_process_executor_primitive_config():
    @executor(name="test_executor", config_schema=str)
    def test_executor(init_context):
        from dagster.core.executor.in_process import InProcessExecutor

        assert init_context.executor_config == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=Retries.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    assert_pipeline_runs_with_executor(
        [test_executor], {"test_executor": {"config": "secret testing value!!"}}
    )


def test_in_process_executor_dict_config():
    @executor(name="test_executor", config_schema={"value": str})
    def test_executor(init_context):
        from dagster.core.executor.in_process import InProcessExecutor

        assert init_context.executor_config["value"] == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=Retries.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    assert_pipeline_runs_with_executor(
        [test_executor], {"test_executor": {"config": {"value": "secret testing value!!"}}}
    )


def test_in_process_executor_dict_config_configured():
    @executor(name="test_executor", config_schema={"value": str})
    def test_executor(init_context):
        from dagster.core.executor.in_process import InProcessExecutor

        assert init_context.executor_config["value"] == "secret testing value!!"

        return InProcessExecutor(
            # shouldn't need to .get() here - issue with defaults in config setup
            retries=Retries.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    test_executor_configured = test_executor.configured(
        {"value": "secret testing value!!"}, "configured_test_executor"
    )

    assert_pipeline_runs_with_executor(
        [test_executor_configured], {"configured_test_executor": None}
    )


@solid
def emit_one(_):
    return 1


@pipeline(
    mode_defs=[
        ModeDefinition(
            executor_defs=[multiprocess_executor.configured({"max_concurrent": 1})],
            resource_defs={"io_manager": fs_io_manager},
        )
    ]
)
def multiproc_test():
    emit_one()


def test_multiproc():

    with instance_for_test() as instance:

        result = execute_pipeline(
            reconstructable(multiproc_test),
            run_config={
                "resources": {
                    "io_manager": {
                        "config": {"base_dir": path.join(instance.root_directory, "storage")}
                    }
                },
            },
            instance=instance,
        )
        assert result.success


def test_defaulting_behavior():
    # selects in_process from the default mode
    @pipeline
    def default():
        pass

    result = execute_pipeline(default)
    assert result.success

    # selects single if only one present
    @pipeline(
        mode_defs=[
            ModeDefinition(
                executor_defs=[
                    in_process_executor.configured(
                        {"retries": {"disabled": {}}}, name="my_executor"
                    )
                ]
            )
        ]
    )
    def custom_executor():
        pass

    result = execute_pipeline(custom_executor)
    assert result.success

    # defaults to system in_process if present
    @pipeline(
        mode_defs=[
            ModeDefinition(
                executor_defs=[
                    in_process_executor,
                    in_process_executor.configured(
                        {"retries": {"disabled": {}}}, name="my_executor"
                    ),
                ]
            )
        ]
    )
    def has_default():
        pass

    result = execute_pipeline(has_default)
    assert result.success

    # fails at config time if multiple options and not selected
    @pipeline(
        mode_defs=[
            ModeDefinition(
                executor_defs=[
                    in_process_executor.configured(
                        {"retries": {"disabled": {}}}, name="my_executor"
                    ),
                    in_process_executor.configured(
                        {"retries": {"enabled": {}}}, name="my_other_executor"
                    ),
                ]
            )
        ]
    )
    def executor_options():
        pass

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(executor_options)

    result = execute_pipeline(executor_options, run_config={"execution": {"my_other_executor": {}}})
    assert result.success

    @executor(config_schema=str)
    def needs_config(_):
        from dagster.core.executor.in_process import InProcessExecutor

        return InProcessExecutor(
            retries=Retries.from_config({"enabled": {}}),
            marker_to_close=None,
        )

    @pipeline(mode_defs=[ModeDefinition(executor_defs=[needs_config])])
    def one_but_needs_config():
        pass

    with pytest.raises(DagsterInvalidConfigError):
        execute_pipeline(one_but_needs_config)
