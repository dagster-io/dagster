from dagster import (
    DagsterInstance,
    execute_pipeline,
    execute_solid,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.test_utils import instance_for_test


@solid
def always_blue(_):
    return "blue"


@pipeline
def predict_color():
    always_blue()


# start_exec_pipeline
def test_execute_pipeline():
    result = execute_pipeline(predict_color)
    assert result.success
    assert result.output_for_solid("always_blue") == "blue"


# end_exec_pipeline

# start_exec_solid
def test_execute_solid():
    result = execute_solid(always_blue)
    assert result.success
    assert result.output_value() == "blue"


# end_exec_solid


def script_example():
    with instance_for_test():
        # start_script
        execute_pipeline(predict_color, instance=DagsterInstance.get())
        # end_script


# start_multi_proc
def test_multiprocess_executor():
    result = execute_pipeline(
        run_config={
            # This section controls how the run will be executed.
            # The multiprocess executor runs each step in its own sub process.
            "execution": {"multiprocess": {}},
            # This section controls how values will be passed from one solid to the next.
            # The default is in memory, so here we set it to filesystem to allow the
            # separate subprocess to get the values
            "intermediate_storage": {"filesystem": {}},
        },
        # The default instance for this API is an in memory ephemeral one.
        # To allow the multiple processes to coordinate we use one here
        # backed by a temporary directory.
        instance=DagsterInstance.local_temp(),
        # A ReconstructablePipeline is necessary to load the pipeline in child processes.
        # reconstructable() is a utility function that captures where the
        # PipelineDefinition came from.
        pipeline=reconstructable(predict_color),
    )
    assert result.success


# end_multi_proc
