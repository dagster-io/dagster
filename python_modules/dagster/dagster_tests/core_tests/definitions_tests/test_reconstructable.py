import re
import sys
import types

import pytest

from dagster import (
    DagsterInvariantViolationError,
    GraphDefinition,
    JobDefinition,
    execute_job,
    job,
    op,
    reconstructable,
    repository,
)
from dagster._core.code_pointer import FileCodePointer
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    PipelinePythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.snap import PipelineSnapshot, create_pipeline_snapshot_id
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path
from dagster._utils.hosted_user_process import recon_pipeline_from_origin


@op
def the_op():
    return 1


@job
def the_job():
    the_op()


def get_the_pipeline():
    return the_job


def not_the_pipeline():
    return None


def get_with_args(_x):
    return the_job


lambda_version = lambda: the_job


def pid(pipeline_def):
    return create_pipeline_snapshot_id(PipelineSnapshot.from_pipeline_def(pipeline_def))


@job
def some_job():
    pass


@repository
def some_repo():
    return [some_job]


def test_function():
    recon_pipe = reconstructable(get_the_pipeline)
    assert pid(recon_pipe.get_definition()) == pid(the_job)


def test_decorator():
    recon_pipe = reconstructable(the_job)
    assert pid(recon_pipe.get_definition()) == pid(the_job)


def test_lambda():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Reconstructable target can not be a lambda",
    ):
        reconstructable(lambda_version)


def test_not_defined_in_module(mocker):
    mocker.patch("inspect.getmodule", return_value=types.ModuleType("__main__"))
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "reconstructable() can not reconstruct jobs or pipelines defined in interactive environments"
        ),
    ):
        reconstructable(get_the_pipeline)


def test_manual_instance():
    defn = JobDefinition(graph_def=GraphDefinition(node_defs=[the_op], name="test"))
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Reconstructable target was not a function returning a job definition, or a job definition produced by a decorated function.",
    ):
        reconstructable(defn)


def test_args_fails():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Reconstructable target must be callable with no arguments",
    ):
        reconstructable(get_with_args)


def test_bad_target():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Loadable attributes must be either a JobDefinition, GraphDefinition, PipelineDefinition, "
            "AssetGroup, or RepositoryDefinition. Got None."
        ),
    ):
        reconstructable(not_the_pipeline)


def test_inner_scope():
    def get_the_pipeline_inner():
        return the_job

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Use a function or decorated function defined at module scope",
    ):
        reconstructable(get_the_pipeline_inner)


def test_inner_decorator():
    @job
    def pipe():
        the_op()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Use a function or decorated function defined at module scope",
    ):
        reconstructable(pipe)


def test_solid_selection():
    recon_pipe = reconstructable(get_the_pipeline)
    sub_pipe_full = recon_pipe.subset_for_execution(["the_op"], asset_selection=None)
    assert sub_pipe_full.solid_selection == ["the_op"]

    sub_pipe_unresolved = recon_pipe.subset_for_execution(["the_op+"], asset_selection=None)
    assert sub_pipe_unresolved.solid_selection == ["the_op+"]


def test_reconstructable_module():
    original_sys_path = sys.path
    try:
        sys.path.insert(0, file_relative_path(__file__, "."))
        from foo import bar_job  # pylint: disable=import-error

        reconstructable(bar_job)

    finally:
        sys.path = original_sys_path


def test_reconstruct_from_origin():
    origin = PipelinePythonOrigin(
        pipeline_name="foo_pipe",
        repository_origin=RepositoryPythonOrigin(
            executable_path="my_python",
            code_pointer=FileCodePointer(
                python_file="foo.py",
                fn_name="bar",
                working_directory="/",
            ),
            container_image="my_image",
            entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
            container_context={"docker": {"registry": "my_reg"}},
        ),
    )

    recon_pipeline = recon_pipeline_from_origin(origin)

    assert recon_pipeline.pipeline_name == origin.pipeline_name
    assert recon_pipeline.repository.pointer == origin.repository_origin.code_pointer
    assert recon_pipeline.repository.container_image == origin.repository_origin.container_image
    assert recon_pipeline.repository.executable_path == origin.repository_origin.executable_path
    assert recon_pipeline.repository.container_context == origin.repository_origin.container_context


def test_reconstructable_memoize():
    recon_job = reconstructable(some_job)

    # warm the cache
    recon_job.get_definition()
    starting_misses = ReconstructableJob.get_definition.cache_info().misses
    with instance_for_test() as instance:
        result = execute_job(recon_job, instance=instance)

    assert result.success

    # ensure the definition was not re-fetched during execution (at least in this process)
    assert ReconstructableJob.get_definition.cache_info().misses == starting_misses

    # if this starts failing, the need for the lru_cache is gone
    assert ReconstructableJob.get_definition.cache_info().hits > 1
