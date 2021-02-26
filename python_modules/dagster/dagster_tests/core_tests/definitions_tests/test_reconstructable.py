import os
import re
import sys
import types

import pytest
from dagster import DagsterInvariantViolationError, PipelineDefinition, lambda_solid, pipeline
from dagster.core.definitions.reconstructable import ReconstructableRepository, reconstructable
from dagster.core.snap import PipelineSnapshot, create_pipeline_snapshot_id
from dagster.utils import file_relative_path


@lambda_solid
def the_solid():
    return 1


@pipeline
def the_pipeline():
    the_solid()


def get_the_pipeline():
    return the_pipeline


def not_the_pipeline():
    return None


def get_with_args(_x):
    return the_pipeline


lambda_version = lambda: the_pipeline


def pid(pipeline_def):
    return create_pipeline_snapshot_id(PipelineSnapshot.from_pipeline_def(pipeline_def))


def test_function():
    recon_pipe = reconstructable(get_the_pipeline)
    assert pid(recon_pipe.get_definition()) == pid(the_pipeline)


def test_decorator():
    recon_pipe = reconstructable(the_pipeline)
    assert pid(recon_pipe.get_definition()) == pid(the_pipeline)


def test_lambda():
    with pytest.raises(
        DagsterInvariantViolationError, match="Reconstructable target can not be a lambda"
    ):
        reconstructable(lambda_version)


def test_not_defined_in_module(mocker):
    mocker.patch("inspect.getmodule", return_value=types.ModuleType("__main__"))
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "reconstructable() can not reconstruct pipelines defined in interactive environments"
        ),
    ):
        reconstructable(get_the_pipeline)


def test_manual_instance():
    defn = PipelineDefinition([the_solid])
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Reconstructable target should be a function or definition produced by a decorated function",
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
            "Loadable attributes must be either a PipelineDefinition or a "
            "RepositoryDefinition. Got None."
        ),
    ):
        reconstructable(not_the_pipeline)


def test_inner_scope():
    def get_the_pipeline_inner():
        return the_pipeline

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Use a function or decorated function defined at module scope",
    ):
        reconstructable(get_the_pipeline_inner)


def test_inner_decorator():
    @pipeline
    def pipe():
        the_solid()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Use a function or decorated function defined at module scope",
    ):
        reconstructable(pipe)


def test_reconstructable_cli_args():
    recon_file = ReconstructableRepository.for_file(
        "foo_file", "bar_function", "/path/to/working_dir"
    )
    assert (
        recon_file.get_cli_args()
        == "-f {foo_file} -a bar_function -d {working_directory}".format(
            foo_file=os.path.abspath(os.path.expanduser("foo_file")),
            working_directory=os.path.abspath(os.path.expanduser("/path/to/working_dir")),
        )
    )
    recon_file = ReconstructableRepository.for_file("foo_file", "bar_function")
    assert recon_file.get_cli_args() == "-f {foo_file} -a bar_function -d {working_dir}".format(
        foo_file=os.path.abspath(os.path.expanduser("foo_file")), working_dir=os.getcwd()
    )
    recon_module = ReconstructableRepository.for_module("foo_module", "bar_function")
    assert recon_module.get_cli_args() == "-m foo_module -a bar_function"


def test_solid_selection():
    recon_pipe = reconstructable(get_the_pipeline)
    sub_pipe_full = recon_pipe.subset_for_execution(["the_solid"])
    assert sub_pipe_full.solids_to_execute == {"the_solid"}

    sub_pipe_unresolved = recon_pipe.subset_for_execution(["the_solid+"])
    assert sub_pipe_unresolved.solids_to_execute == {"the_solid"}


def test_reconstructable_module():
    original_sys_path = sys.path
    try:
        sys.path.insert(0, file_relative_path(__file__, "."))
        from foo import bar_pipeline  # pylint: disable=import-error

        reconstructable(bar_pipeline)

    finally:
        sys.path = original_sys_path
