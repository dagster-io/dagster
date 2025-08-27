import re
import sys
import types

import dagster as dg
import pytest
from dagster._core.code_pointer import FileCodePointer
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    JobPythonOrigin,
    RepositoryPythonOrigin,
)
from dagster._core.snap import JobSnap
from dagster._utils.hosted_user_process import recon_job_from_origin


@dg.op
def the_op():
    return 1


@dg.job
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
    return JobSnap.from_job_def(pipeline_def).snapshot_id


@dg.job
def some_job():
    pass


@dg.repository
def some_repo():
    return [some_job]


def test_function():
    recon_pipe = dg.reconstructable(get_the_pipeline)
    assert pid(recon_pipe.get_definition()) == pid(the_job)


def test_decorator():
    recon_pipe = dg.reconstructable(the_job)
    assert pid(recon_pipe.get_definition()) == pid(the_job)


def test_lambda():
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Reconstructable target can not be a lambda",
    ):
        dg.reconstructable(lambda_version)


def test_not_defined_in_module(mocker):
    mocker.patch("inspect.getmodule", return_value=types.ModuleType("__main__"))
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "reconstructable() can not reconstruct jobs defined in interactive environments"
        ),
    ):
        dg.reconstructable(get_the_pipeline)


def test_manual_instance():
    defn = dg.JobDefinition(graph_def=dg.GraphDefinition(node_defs=[the_op], name="test"))
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "Reconstructable target was not a function returning a job definition, or a job"
            " definition produced by a decorated function."
        ),
    ):
        dg.reconstructable(defn)


def test_args_fails():
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Reconstructable target must be callable with no arguments",
    ):
        dg.reconstructable(get_with_args)


def test_bad_target():
    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape(
            "Loadable attributes must be either a JobDefinition, GraphDefinition, Definitions,"
            " or RepositoryDefinition. Got None."
        ),
    ):
        dg.reconstructable(not_the_pipeline)  # pyright: ignore[reportArgumentType]


def test_inner_scope():
    def get_the_pipeline_inner():
        return the_job

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Use a function or decorated function defined at module scope",
    ):
        dg.reconstructable(get_the_pipeline_inner)


def test_inner_decorator():
    @dg.job
    def pipe():
        the_op()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Use a function or decorated function defined at module scope",
    ):
        dg.reconstructable(pipe)


def test_op_selection():
    recon_pipe = dg.reconstructable(get_the_pipeline)
    sub_pipe_full = recon_pipe.get_subset(op_selection={"the_op"})
    assert sub_pipe_full.op_selection == {"the_op"}

    sub_pipe_unresolved = recon_pipe.get_subset(op_selection={"the_op+"})
    assert sub_pipe_unresolved.op_selection == {"the_op+"}


def test_reconstructable_module():
    original_sys_path = sys.path
    try:
        sys.path.insert(0, dg.file_relative_path(__file__, "."))
        from foo import bar_job  # type: ignore

        dg.reconstructable(bar_job)

    finally:
        sys.path = original_sys_path


def test_reconstruct_from_origin():
    origin = JobPythonOrigin(
        job_name="foo_pipe",
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

    recon_job = recon_job_from_origin(origin)

    assert recon_job.job_name == origin.job_name
    assert recon_job.repository.pointer == origin.repository_origin.code_pointer
    assert recon_job.repository.container_image == origin.repository_origin.container_image
    assert recon_job.repository.executable_path == origin.repository_origin.executable_path
    assert recon_job.repository.container_context == origin.repository_origin.container_context


def test_reconstructable_memoize() -> None:
    recon_job = dg.reconstructable(some_job)

    # warm the cache
    recon_job.get_definition()
    starting_misses = ReconstructableJob.get_definition.cache_info().misses
    with dg.instance_for_test() as instance:
        result = dg.execute_job(recon_job, instance=instance)

    assert result.success

    # ensure the definition was not re-fetched during execution (at least in this process)
    assert ReconstructableJob.get_definition.cache_info().misses == starting_misses

    # if this starts failing, the need for the lru_cache is gone
    assert ReconstructableJob.get_definition.cache_info().hits > 1
