"""isort:skip_file"""

# start_pipeline_marker

from dagster import pipeline, solid


@solid
def return_one():
    return 1


@solid
def add_two(i: int):
    return i + 2


@solid
def multi_three(i: int):
    return i * 3


@pipeline
def my_pipeline():
    multi_three(add_two(return_one()))


# end_pipeline_marker

# start_execute_marker
from dagster import execute_pipeline

if __name__ == "__main__":
    result = execute_pipeline(my_pipeline)

# end_execute_marker


def execute_subset():
    # start_solid_selection_marker
    execute_pipeline(my_pipeline, solid_selection=["*add_two"])
    # end_solid_selection_marker


@solid
def total(in_1: int, in_2: int, in_3: int, in_4: int):
    return in_1 + in_2 + in_3 + in_4


from dagster import ModeDefinition, fs_io_manager

# start_parallel_pipeline_marker
@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def parallel_pipeline():
    total(return_one(), return_one(), return_one(), return_one())


# end_parallel_pipeline_marker

# start_multiprocessing_marker


def execute_multiprocessing():
    from dagster import reconstructable, DagsterInstance

    execute_pipeline(
        # A ReconstructablePipeline is necessary to load the pipeline in child processes.
        # reconstructable() is a utility function that captures where the
        # PipelineDefinition came from.
        reconstructable(parallel_pipeline),
        run_config={
            # This section controls how the run will be executed.
            # The multiprocess executor runs each solid in its own sub process.
            "execution": {"multiprocess": {}},
        },
        # The default instance for this API is an in memory ephemeral one.
        # To allow the multiple processes to coordinate we use one here
        # backed by a temporary directory.
        instance=DagsterInstance.local_temp(),
    )


# end_multiprocessing_marker
