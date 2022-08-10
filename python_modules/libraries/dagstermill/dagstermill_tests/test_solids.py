import importlib.util
import os
import pickle
import tempfile
from contextlib import contextmanager

import nbformat
import pytest
from dagstermill import DagstermillError
from dagstermill.compat import ExecutionError
from dagstermill.factory import define_dagstermill_op
from jupyter_client.kernelspec import NoSuchKernel
from nbconvert.preprocessors import ExecutePreprocessor

from dagster._check import CheckError
from dagster._core.definitions.metadata import PathMetadataValue
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.test_utils import instance_for_test
from dagster._legacy import execute_pipeline, pipeline
from dagster._utils import file_relative_path, safe_tempfile_path

DAGSTER_PANDAS_PRESENT = importlib.util.find_spec("dagster_pandas") is not None
SKLEARN_PRESENT = importlib.util.find_spec("sklearn") is not None
MATPLOTLIB_PRESENT = importlib.util.find_spec("matplotlib") is not None


def get_path(materialization_event):
    for (
        metadata_entry
    ) in materialization_event.event_specific_data.materialization.metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataValue):
            return metadata_entry.entry_data.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.step_event_list if x.event_type_value == "ASSET_MATERIALIZATION"
    ]
    for materialization_event in materialization_events:
        result_path = get_path(materialization_event)
        if os.path.exists(result_path):
            os.unlink(result_path)


@contextmanager
def exec_for_test(fn_name, env=None, raise_on_error=True, **kwargs):
    result = None
    recon_pipeline = ReconstructablePipeline.for_module("dagstermill.examples.repository", fn_name)

    with instance_for_test() as instance:
        try:
            result = execute_pipeline(
                recon_pipeline,
                env,
                instance=instance,
                raise_on_error=raise_on_error,
                **kwargs,
            )
            yield result
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.notebook_test
def test_hello_world():
    with exec_for_test("build_hello_world_job") as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_with_config():
    with exec_for_test("hello_world_config_job") as result:
        assert result.success
        assert result.output_for_solid("hello_world_config") == "hello"


@pytest.mark.notebook_test
def test_hello_world_with_config_escape():
    with exec_for_test(
        "hello_world_config_job",
        env={"solids": {"hello_world_config": {"config": {"greeting": "'"}}}},
    ) as result:
        assert result.success
        assert result.output_for_solid("hello_world_config") == "'"

    with exec_for_test(
        "hello_world_config_job",
        env={"solids": {"hello_world_config": {"config": {"greeting": '"'}}}},
    ) as result:
        assert result.success
        assert result.output_for_solid("hello_world_config") == '"'

    with exec_for_test(
        "hello_world_config_job",
        env={"solids": {"hello_world_config": {"config": {"greeting": "\\"}}}},
    ) as result:
        assert result.success
        assert result.output_for_solid("hello_world_config") == "\\"

    with exec_for_test(
        "hello_world_config_job",
        env={"solids": {"hello_world_config": {"config": {"greeting": "}"}}}},
    ) as result:
        assert result.success
        assert result.output_for_solid("hello_world_config") == "}"

    with exec_for_test(
        "hello_world_config_job",
        env={"solids": {"hello_world_config": {"config": {"greeting": "\n"}}}},
    ) as result:
        assert result.success
        assert result.output_for_solid("hello_world_config") == "\n"


@pytest.mark.notebook_test
def test_alias_with_config():
    with exec_for_test(
        "alias_config_job",
        env={"solids": {"aliased_greeting": {"config": {"greeting": "boo"}}}},
    ) as result:
        assert result.success
        assert result.output_for_solid("aliased_greeting") == "boo"


@pytest.mark.notebook_test
def test_reexecute_result_notebook():
    def _strip_execution_metadata(nb):
        cells = nb["cells"]
        for cell in cells:
            if "metadata" in cell:
                if "execution" in cell["metadata"]:
                    del cell["metadata"]["execution"]
        nb["cells"] = cells

        return nb

    with exec_for_test(
        "hello_world_job",
        {"loggers": {"console": {"config": {"log_level": "ERROR"}}}},
    ) as result:
        assert result.success

        materialization_events = [
            x for x in result.step_event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        for materialization_event in materialization_events:
            result_path = get_path(materialization_event)

        if result_path.endswith(".ipynb"):
            with open(result_path, encoding="utf8") as fd:
                nb = nbformat.read(fd, as_version=4)
            ep = ExecutePreprocessor()
            ep.preprocess(nb)
            with open(result_path, encoding="utf8") as fd:
                expected = _strip_execution_metadata(nb)
                actual = _strip_execution_metadata(nbformat.read(fd, as_version=4))
                assert actual == expected


@pytest.mark.notebook_test
def test_hello_world_with_output():
    with exec_for_test("hello_world_output_job") as result:
        assert result.success
        assert result.result_for_solid("hello_world_output").output_value() == "hello, world"


@pytest.mark.notebook_test
def test_hello_world_explicit_yield():
    with exec_for_test("hello_world_explicit_yield_job") as result:
        materializations = [
            x for x in result.event_list if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 2
        assert get_path(materializations[1]) == "/path/to/file"


@pytest.mark.notebook_test
def test_add_job():
    with exec_for_test(
        "add_job", {"loggers": {"console": {"config": {"log_level": "ERROR"}}}}
    ) as result:
        assert result.success
        assert result.result_for_solid("add_two_numbers").output_value() == 3


@pytest.mark.notebook_test
def test_double_add_job():
    with exec_for_test(
        "double_add_job",
        {"loggers": {"console": {"config": {"log_level": "ERROR"}}}},
    ) as result:
        assert result.success
        assert result.result_for_solid("add_two_numbers_1").output_value() == 3
        assert result.result_for_solid("add_two_numbers_2").output_value() == 7


@pytest.mark.notebook_test
def test_fan_in_notebook_job():
    with exec_for_test(
        "fan_in_notebook_job",
        {
            "execution": {"multiprocess": {}},
            "solids": {
                "solid_1": {"inputs": {"obj": "hello"}},
                "solid_2": {"inputs": {"obj": "world"}},
            },
        },
    ) as result:
        assert result.success
        assert result.result_for_solid("solid_1").output_value() == "hello"
        assert result.result_for_solid("solid_2").output_value() == "world"
        assert result.result_for_solid("fan_in").output_value() == "hello world"


@pytest.mark.notebook_test
def test_composite_job():
    with exec_for_test(
        "composite_job",
        {
            "execution": {"multiprocess": {}},
            "solids": {"outer": {"solids": {"yield_something": {"inputs": {"obj": "hello"}}}}},
        },
    ) as result:
        assert result.success
        assert (
            result.result_for_solid("outer").result_for_solid("yield_something").output_value()
            == "hello"
        )


@pytest.mark.notebook_test
def test_fan_in_notebook_job_in_mem():
    with exec_for_test(
        "fan_in_notebook_job_in_mem",
        {
            "solids": {
                "solid_1": {"inputs": {"obj": "hello"}},
                "solid_2": {"inputs": {"obj": "world"}},
            },
        },
        raise_on_error=False,
    ) as result:
        # # TODO error at definition time that dagstermill solids require "multiprocessing.shared_memory"
        assert not result.success


@pytest.mark.notebook_test
def test_notebook_dag():
    with exec_for_test(
        "notebook_dag_pipeline",
        {"solids": {"load_a": {"config": 1}, "load_b": {"config": 2}}},
    ) as result:
        assert result.success
        assert result.result_for_solid("add_two_numbers").output_value() == 3
        assert result.result_for_solid("mult_two_numbers").output_value() == 6


@pytest.mark.notebook_test
def test_error_notebook():
    with pytest.raises(ExecutionError) as exc:
        with exec_for_test("error_job") as result:
            pass

    assert "Someone set up us the bomb" in str(exc.value)

    with exec_for_test("error_job", raise_on_error=False) as result:
        assert not result.success
        assert result.step_event_list[1].event_type.value == "STEP_FAILURE"


@pytest.mark.nettest
@pytest.mark.notebook_test
@pytest.mark.skipif(
    not (DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT),
    reason="tutorial_job reqs not present: dagster_pandas, sklearn, matplotlib",
)
def test_tutorial_job():
    with exec_for_test(
        "tutorial_job",
        {"loggers": {"console": {"config": {"log_level": "DEBUG"}}}},
    ) as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_reexecution():
    with exec_for_test("hello_world_job") as result:
        assert result.success

        output_notebook_path = get_path(
            [x for x in result.step_event_list if x.event_type_value == "ASSET_MATERIALIZATION"][0]
        )

        with tempfile.NamedTemporaryFile("w+", suffix=".py") as reexecution_notebook_file:
            reexecution_notebook_file.write(
                (
                    "from dagster import job\n"
                    "from dagstermill.factory import define_dagstermill_op\n\n\n"
                    "reexecution_op = define_dagstermill_op(\n"
                    "    'hello_world_reexecution', '{output_notebook_path}'\n"
                    ")\n\n"
                    "@job\n"
                    "def reexecution_job():\n"
                    "    reexecution_job()\n"
                ).format(output_notebook_path=output_notebook_path)
            )
            reexecution_notebook_file.flush()

            result = None
            reexecution_job = ReconstructablePipeline.for_file(
                reexecution_notebook_file.name, "reexecution_job"
            )

            reexecution_result = None
            with instance_for_test() as instance:
                try:
                    reexecution_result = execute_pipeline(reexecution_job, instance=instance)
                    assert reexecution_result.success
                finally:
                    if reexecution_result:
                        cleanup_result_notebook(reexecution_result)


@pytest.mark.notebook_test
def test_resources_notebook():
    with safe_tempfile_path() as path:
        with exec_for_test(
            "resource_job",
            {"resources": {"list": {"config": path}}},
        ) as result:
            assert result.success

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, "rb") as fd:
                messages = pickle.load(fd)

            messages = [message.split(": ") for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 2
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == "Opened"
            assert msgs[4] == msgs[5] == "Closed"
            assert msgs[1] == "Hello, solid!"
            assert msgs[3] == "Hello, notebook!"


# https://github.com/dagster-io/dagster/issues/3722
@pytest.mark.skip
@pytest.mark.notebook_test
def test_resources_notebook_with_exception():
    result = None
    with safe_tempfile_path() as path:
        with exec_for_test(
            "resource_with_exception_pipeline",
            {"resources": {"list": {"config": path}}},
            raise_on_error=False,
        ) as result:
            assert not result.success
            assert result.step_event_list[8].event_type.value == "STEP_FAILURE"
            assert (
                "raise Exception()"
                in result.step_event_list[8].event_specific_data.error.cause.message
            )

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, "rb") as fd:
                messages = pickle.load(fd)

            messages = [message.split(": ") for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 2
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == "Opened"
            assert msgs[4] == msgs[5] == "Closed"
            assert msgs[1] == "Hello, solid!"
            assert msgs[3] == "Hello, notebook!"


@pytest.mark.notebook_test
def test_bad_kernel_job():
    with pytest.raises(NoSuchKernel):
        with exec_for_test("bad_kernel_job"):
            pass


@pytest.mark.notebook_test
def test_hello_logging():
    with exec_for_test("hello_logging_job") as result:
        assert result.success


@pytest.mark.notebook_test
def test_reimport():
    with exec_for_test("reimport_job") as result:
        assert result.success
        assert result.result_for_solid("reimport").output_value() == 6


@pytest.mark.notebook_test
def test_yield_3_job():
    with exec_for_test("yield_3_job") as result:
        assert result.success
        assert result.result_for_solid("yield_3").output_value() == 3


@pytest.mark.notebook_test
def test_yield_obj_job():
    with exec_for_test("yield_obj_job") as result:
        assert result.success
        assert result.result_for_solid("yield_obj").output_value().x == 3


@pytest.mark.notebook_test
def test_hello_world_with_custom_tags_and_description_job():
    with exec_for_test("hello_world_with_custom_tags_and_description_job") as result:
        assert result.success


def test_non_reconstructable_job():
    foo_solid = define_dagstermill_op("foo", file_relative_path(__file__, "notebooks/foo.ipynb"))

    @pipeline
    def non_reconstructable():
        foo_solid()

    with pytest.raises(DagstermillError, match="job that is not reconstructable."):
        execute_pipeline(non_reconstructable)


# Test Solid Tags & Description

BACKING_NB_NAME = "hello_world"
BACKING_NB_PATH = file_relative_path(__file__, f"notebooks/{BACKING_NB_NAME}.ipynb")


def test_default_tags():
    test_solid_default_tags = define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH)

    assert test_solid_default_tags.tags == {
        "kind": "ipynb",
        "notebook_path": BACKING_NB_PATH,
    }


def test_custom_tags():
    test_solid_custom_tags = define_dagstermill_op(
        BACKING_NB_NAME, BACKING_NB_PATH, tags={"foo": "bar"}
    )

    assert test_solid_custom_tags.tags == {
        "kind": "ipynb",
        "notebook_path": BACKING_NB_PATH,
        "foo": "bar",
    }


def test_reserved_tags_not_overridden():
    with pytest.raises(CheckError, match="key is reserved for use by Dagster"):
        define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH, tags={"notebook_path": "~"})

    with pytest.raises(CheckError, match="key is reserved for use by Dagster"):
        define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH, tags={"kind": "py"})


def test_default_description():
    test_solid = define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH)
    assert test_solid.description.startswith("This op is backed by the notebook at ")


def test_custom_description():
    test_description = "custom description"
    test_solid = define_dagstermill_op(
        BACKING_NB_NAME, BACKING_NB_PATH, description=test_description
    )
    assert test_solid.description == test_description


@pytest.mark.notebook_test
def test_retries(capsys):
    with exec_for_test("retries_job", raise_on_error=False) as result:

        assert result.result_for_solid("yield_retry").retry_attempts == 1

        # the raise_retry solid should trigger a warning to use yield_event
        warn_found = False
        captured = capsys.readouterr()
        for line in captured.err.split("\n"):
            if "Use dagstermill.yield_event with RetryRequested or Failure" in line:
                warn_found = True

        assert warn_found


@pytest.mark.notebook_test
def test_failure(capsys):
    with exec_for_test("failure_job", raise_on_error=False) as result:
        assert (
            result.result_for_solid("yield_failure").failure_data.user_failure_data.description
            == "bad bad notebook"
        )

        # the raise_failure solid should trigger a warning to use yield_event
        warn_found = False
        captured = capsys.readouterr()
        for line in captured.err.split("\n"):
            if "Use dagstermill.yield_event with RetryRequested or Failure" in line:
                warn_found = True

        assert warn_found


@pytest.mark.notebook_test
def test_hello_world_graph():
    from dagstermill.examples.repository import build_hello_world_job

    from dagster import reconstructable

    with instance_for_test() as instance:
        result = None
        try:
            result = execute_pipeline(
                reconstructable(build_hello_world_job),
                instance=instance,
            )
            assert result.success
        finally:
            if result:
                cleanup_result_notebook(result)
