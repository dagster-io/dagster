import importlib.util
import os
import pickle
import tempfile
from contextlib import contextmanager

import nbformat
import pytest
from dagster import execute_job, job
from dagster._check import CheckError
from dagster._core.definitions.metadata import NotebookMetadataValue, PathMetadataValue
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path, safe_tempfile_path
from dagstermill import DagstermillError
from dagstermill.compat import ExecutionError
from dagstermill.examples.repository import custom_io_mgr_key_job
from dagstermill.factory import define_dagstermill_op
from jupyter_client.kernelspec import NoSuchKernel
from nbconvert.preprocessors import ExecutePreprocessor

DAGSTER_PANDAS_PRESENT = importlib.util.find_spec("dagster_pandas") is not None
SKLEARN_PRESENT = importlib.util.find_spec("sklearn") is not None
MATPLOTLIB_PRESENT = importlib.util.find_spec("matplotlib") is not None


def get_path(materialization_event):
    for (
        metadata_entry
    ) in materialization_event.event_specific_data.materialization.metadata_entries:
        if isinstance(metadata_entry.value, (PathMetadataValue, NotebookMetadataValue)):
            return metadata_entry.value.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
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
            with execute_job(
                job=recon_pipeline,
                run_config=env,
                instance=instance,
                raise_on_error=raise_on_error,
                **kwargs,
            ) as result:
                yield result
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.notebook_test
def test_hello_world():
    with exec_for_test("hello_world_job") as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_job():
    with exec_for_test("hello_world_job") as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_with_config():
    with exec_for_test("hello_world_config_job") as result:
        assert result.success
        assert result.output_for_node("hello_world_config") == "hello"


@pytest.mark.notebook_test
def test_hello_world_with_config_escape():
    with exec_for_test(
        "hello_world_config_job",
        env={"ops": {"hello_world_config": {"config": {"greeting": "'"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("hello_world_config") == "'"

    with exec_for_test(
        "hello_world_config_job",
        env={"ops": {"hello_world_config": {"config": {"greeting": '"'}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("hello_world_config") == '"'

    with exec_for_test(
        "hello_world_config_job",
        env={"ops": {"hello_world_config": {"config": {"greeting": "\\"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("hello_world_config") == "\\"

    with exec_for_test(
        "hello_world_config_job",
        env={"ops": {"hello_world_config": {"config": {"greeting": "}"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("hello_world_config") == "}"

    with exec_for_test(
        "hello_world_config_job",
        env={"ops": {"hello_world_config": {"config": {"greeting": "\n"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("hello_world_config") == "\n"


@pytest.mark.notebook_test
def test_alias_with_config():
    with exec_for_test(
        "alias_config_job",
        env={"ops": {"aliased_greeting": {"config": {"greeting": "boo"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("aliased_greeting") == "boo"


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
            x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
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
        assert result.output_for_node("hello_world_output") == "hello, world"


@pytest.mark.notebook_test
def test_hello_world_explicit_yield():
    with exec_for_test("hello_world_explicit_yield_job") as result:
        materializations = [
            x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 2
        assert get_path(materializations[1]) == "/path/to/file"


@pytest.mark.notebook_test
def test_add_job():
    with exec_for_test(
        "add_job", {"loggers": {"console": {"config": {"log_level": "ERROR"}}}}
    ) as result:
        assert result.success
        assert result.output_for_node("add_two_numbers") == 3


@pytest.mark.notebook_test
def test_double_add_job():
    with exec_for_test(
        "double_add_job",
        {"loggers": {"console": {"config": {"log_level": "ERROR"}}}},
    ) as result:
        assert result.success
        assert result.output_for_node("add_two_numbers_1") == 3
        assert result.output_for_node("add_two_numbers_2") == 7


@pytest.mark.notebook_test
def test_fan_in_notebook_job():
    with exec_for_test(
        "fan_in_notebook_job",
        {
            "execution": {"config": {"multiprocess": {}}},
            "ops": {
                "op_1": {"inputs": {"obj": "hello"}},
                "op_2": {"inputs": {"obj": "world"}},
            },
        },
    ) as result:
        assert result.success
        assert result.output_for_node("op_1") == "hello"
        assert result.output_for_node("op_2") == "world"
        assert result.output_for_node("fan_in") == "hello world"


@pytest.mark.notebook_test
def test_graph_job():
    with exec_for_test(
        "graph_job",
        {
            "execution": {"config": {"multiprocess": {}}},
            "ops": {"outer": {"ops": {"yield_something": {"inputs": {"obj": "hello"}}}}},
        },
    ) as result:
        assert result.success
        assert result.output_for_node("outer.yield_something") == "hello"


@pytest.mark.notebook_test
def test_fan_in_notebook_job_in_mem():
    with exec_for_test(
        "fan_in_notebook_job_in_mem",
        {
            "execution": {"config": {"in_process": {}}},
            "ops": {
                "op_1": {"inputs": {"obj": "hello"}},
                "op_2": {"inputs": {"obj": "world"}},
            },
        },
        raise_on_error=False,
    ) as result:
        # # TODO error at definition time that dagstermill ops require "multiprocessing.shared_memory"
        assert not result.success


@pytest.mark.notebook_test
def test_notebook_dag():
    with exec_for_test(
        "notebook_dag_job",
        {"ops": {"load_a": {"config": 1}, "load_b": {"config": 2}}},
    ) as result:
        assert result.success
        assert result.output_for_node("add_two_numbers") == 3
        assert result.output_for_node("mult_two_numbers") == 6


@pytest.mark.notebook_test
def test_error_notebook():
    exec_for_test("error_job")
    with pytest.raises(ExecutionError) as exc:
        with exec_for_test("error_job", {"execution": {"config": {"in_process": {}}}}) as result:
            pass

    assert "Someone set up us the bomb" in str(exc.value)

    with exec_for_test(
        "error_job", {"execution": {"config": {"in_process": {}}}}, raise_on_error=False
    ) as result:
        assert not result.success
        assert len(result.get_failed_step_keys()) > 0

    result = None
    recon_pipeline = ReconstructablePipeline.for_module(
        "dagstermill.examples.repository", "error_job"
    )

    # test that the notebook is saved on failure
    with instance_for_test() as instance:
        try:
            result = execute_job(
                recon_pipeline,
                run_config={"execution": {"config": {"in_process": {}}}},
                instance=instance,
                raise_on_error=False,
            )
            storage_dir = instance.storage_directory()
            files = os.listdir(storage_dir)
            notebook_found = (False,)
            for f in files:
                if "-out.ipynb" in f:
                    notebook_found = True

            assert notebook_found
        finally:
            if result:
                cleanup_result_notebook(result)


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
            [x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"][0]
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
                    "    reexecution_op()\n"
                ).format(output_notebook_path=output_notebook_path)
            )
            reexecution_notebook_file.flush()

            reexecution_job = ReconstructablePipeline.for_file(
                reexecution_notebook_file.name, "reexecution_job"
            )

            reexecution_result = None
            with instance_for_test() as instance:
                try:
                    reexecution_result = execute_job(reexecution_job, instance=instance)
                    assert reexecution_result.success
                finally:
                    if reexecution_result:
                        cleanup_result_notebook(reexecution_result)


@pytest.mark.notebook_test
def test_resources_notebook():
    with safe_tempfile_path() as path:
        with exec_for_test(
            "resource_job",
            {"execution": {"config": {"in_process": {}}}, "resources": {"list": {"config": path}}},
        ) as result:
            assert result.success

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, op!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, "rb") as fd:
                messages = pickle.load(fd)

            messages = [message.split(": ") for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 3
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == "Opened"
            assert msgs[4] == msgs[5] == "Closed"
            assert msgs[1] == "Hello, op!"
            assert msgs[3] == "Hello, notebook!"


# https://github.com/dagster-io/dagster/issues/3722
@pytest.mark.skip
@pytest.mark.notebook_test
def test_resources_notebook_with_exception():
    result = None
    with safe_tempfile_path() as path:
        with exec_for_test(
            "resource_with_exception_job",
            {"execution": {"config": {"in_process": {}}}, "resources": {"list": {"config": path}}},
            raise_on_error=False,
        ) as result:
            assert not result.success
            assert result.all_events[8].event_type.value == "STEP_FAILURE"
            assert (
                "raise Exception()" in result.all_events[8].event_specific_data.error.cause.message
            )

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, op!', '9d438e: Opened',
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
            assert msgs[1] == "Hello, op!"
            assert msgs[3] == "Hello, notebook!"


@pytest.mark.notebook_test
def test_bad_kernel_job():
    with pytest.raises(NoSuchKernel):
        with exec_for_test(
            "bad_kernel_job", {"execution": {"config": {"in_process": {}}}}, raise_on_error=True
        ):
            pass


@pytest.mark.notebook_test
def test_hello_logging():
    with exec_for_test("hello_logging_job") as result:
        assert result.success


@pytest.mark.notebook_test
def test_reimport():
    with exec_for_test("reimport_job") as result:
        assert result.success
        assert result.output_for_node("reimport") == 6


@pytest.mark.notebook_test
def test_yield_3_job():
    with exec_for_test("yield_3_job") as result:
        assert result.success
        assert result.output_for_node("yield_3") == 3


@pytest.mark.notebook_test
def test_yield_obj_job():
    with exec_for_test("yield_obj_job") as result:
        assert result.success
        assert result.output_for_node("yield_obj").x == 3


@pytest.mark.notebook_test
def test_hello_world_with_custom_tags_and_description_job():
    with exec_for_test("hello_world_with_custom_tags_and_description_job") as result:
        assert result.success


def test_non_reconstructable_job():
    foo_op = define_dagstermill_op("foo", file_relative_path(__file__, "notebooks/foo.ipynb"))

    @job
    def non_reconstructable():
        foo_op()

    with pytest.raises(DagstermillError, match="job that is not reconstructable."):
        non_reconstructable.execute_in_process()


# Test Op Tags & Description

BACKING_NB_NAME = "hello_world"
BACKING_NB_PATH = file_relative_path(__file__, f"notebooks/{BACKING_NB_NAME}.ipynb")


def test_default_tags():
    test_op_default_tags = define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH)

    assert test_op_default_tags.tags == {
        "kind": "ipynb",
        "notebook_path": BACKING_NB_PATH,
    }


def test_custom_tags():
    test_op_custom_tags = define_dagstermill_op(
        BACKING_NB_NAME, BACKING_NB_PATH, tags={"foo": "bar"}
    )

    assert test_op_custom_tags.tags == {
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
    test_op = define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH)
    assert test_op.description.startswith("This op is backed by the notebook at ")


def test_custom_description():
    test_description = "custom description"
    test_op = define_dagstermill_op(BACKING_NB_NAME, BACKING_NB_PATH, description=test_description)
    assert test_op.description == test_description


@pytest.mark.notebook_test
def test_retries(capsys):
    with exec_for_test(
        "retries_job", {"execution": {"config": {"in_process": {}}}}, raise_on_error=False
    ) as result:
        assert result.retry_attempts_for_node("yield_retry") == 1

        # the raise_retry op should trigger a warning to use yield_event
        warn_found = False
        captured = capsys.readouterr()
        for line in captured.err.split("\n"):
            if "Use dagstermill.yield_event with RetryRequested or Failure" in line:
                warn_found = True

        assert warn_found


@pytest.mark.notebook_test
def test_failure(capsys):
    with exec_for_test(
        "failure_job", {"execution": {"config": {"in_process": {}}}}, raise_on_error=False
    ) as result:
        assert (
            result.failure_data_for_node("yield_failure").user_failure_data.description
            == "bad bad notebook"
        )

        # the raise_failure op should trigger a warning to use yield_event
        warn_found = False
        captured = capsys.readouterr()
        for line in captured.err.split("\n"):
            if "Use dagstermill.yield_event with RetryRequested or Failure" in line:
                warn_found = True

        assert warn_found


@pytest.mark.notebook_test
def test_hello_world_graph():
    from dagster import reconstructable
    from dagstermill.examples.repository import build_hello_world_job

    with instance_for_test() as instance:
        result = None
        try:
            result = execute_job(
                reconstructable(build_hello_world_job),
                instance=instance,
            )
            assert result.success
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.notebook_test
def test_custom_io_manager_key():
    assert "my_custom_io_manager" in custom_io_mgr_key_job.resource_defs.keys()
    assert "output_notebook_io_manager" not in custom_io_mgr_key_job.resource_defs.keys()
