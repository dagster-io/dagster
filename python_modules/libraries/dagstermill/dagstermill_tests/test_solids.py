import os
import pickle
import tempfile
from contextlib import contextmanager

import nbformat
import pytest
from dagster import execute_pipeline, pipeline
from dagster.check import CheckError
from dagster.core.definitions.events import PathMetadataEntryData
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path, safe_tempfile_path
from dagstermill import DagstermillError, define_dagstermill_solid
from jupyter_client.kernelspec import NoSuchKernel
from nbconvert.preprocessors import ExecutePreprocessor
from papermill import PapermillExecutionError

try:
    import dagster_pandas as _

    DAGSTER_PANDAS_PRESENT = True
except ImportError:
    DAGSTER_PANDAS_PRESENT = False

try:
    import sklearn as _

    SKLEARN_PRESENT = True
except ImportError:
    SKLEARN_PRESENT = False

try:
    import matplotlib as _

    MATPLOTLIB_PRESENT = True
except ImportError:
    MATPLOTLIB_PRESENT = False


def get_path(materialization_event):
    for (
        metadata_entry
    ) in materialization_event.event_specific_data.materialization.metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataEntryData):
            return metadata_entry.entry_data.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.step_event_list if x.event_type_value == "STEP_MATERIALIZATION"
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
                recon_pipeline, env, instance=instance, raise_on_error=raise_on_error, **kwargs
            )
            yield result
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.notebook_test
def test_hello_world():
    with exec_for_test("hello_world_pipeline") as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_with_config():
    with exec_for_test("hello_world_config_pipeline") as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_with_output_notebook():
    with exec_for_test("hello_world_with_output_notebook_pipeline") as result:
        assert result.success
        materializations = [
            x for x in result.event_list if x.event_type_value == "STEP_MATERIALIZATION"
        ]
        assert len(materializations) == 1

        assert result.result_for_solid("hello_world").success
        assert "notebook" in result.result_for_solid("hello_world").output_values
        assert os.path.exists(
            result.result_for_solid("hello_world").output_values["notebook"].path_desc
        )
        assert (
            materializations[0]
            .event_specific_data.materialization.metadata_entries[0]
            .entry_data.path
            == result.result_for_solid("hello_world").output_values["notebook"].path_desc
        )

        assert result.result_for_solid("load_notebook").success
        assert result.result_for_solid("load_notebook").output_value() is True


@pytest.mark.notebook_test
def test_hello_world_with_config_escape():
    with exec_for_test(
        "hello_world_config_pipeline",
        env={"solids": {"hello_world_config": {"config": {"greeting": "'"}}}},
    ) as result:
        assert result.success

    with exec_for_test(
        "hello_world_config_pipeline",
        env={"solids": {"hello_world_config": {"config": {"greeting": '"'}}}},
    ) as result:
        assert result.success

    with exec_for_test(
        "hello_world_config_pipeline",
        env={"solids": {"hello_world_config": {"config": {"greeting": "\\"}}}},
    ) as result:
        assert result.success

    with exec_for_test(
        "hello_world_config_pipeline",
        env={"solids": {"hello_world_config": {"config": {"greeting": "}"}}}},
    ) as result:
        assert result.success

    with exec_for_test(
        "hello_world_config_pipeline",
        env={"solids": {"hello_world_config": {"config": {"greeting": "\n"}}}},
    ) as result:
        assert result.success


@pytest.mark.notebook_test
def test_reexecute_result_notebook():
    with exec_for_test(
        "hello_world_pipeline", {"loggers": {"console": {"config": {"log_level": "ERROR"}}}}
    ) as result:
        assert result.success

        materialization_events = [
            x for x in result.step_event_list if x.event_type_value == "STEP_MATERIALIZATION"
        ]
        for materialization_event in materialization_events:
            result_path = get_path(materialization_event)

        if result_path.endswith(".ipynb"):
            with open(result_path) as fd:
                nb = nbformat.read(fd, as_version=4)
            ep = ExecutePreprocessor()
            ep.preprocess(nb, {})
            with open(result_path) as fd:
                assert nbformat.read(fd, as_version=4) == nb


@pytest.mark.notebook_test
def test_hello_world_with_output():
    with exec_for_test("hello_world_output_pipeline") as result:
        assert result.success
        assert result.result_for_solid("hello_world_output").output_value() == "hello, world"


@pytest.mark.notebook_test
def test_hello_world_explicit_yield():
    with exec_for_test("hello_world_explicit_yield_pipeline") as result:
        materializations = [
            x for x in result.event_list if x.event_type_value == "STEP_MATERIALIZATION"
        ]
        assert len(materializations) == 2
        assert get_path(materializations[1]) == "/path/to/file"


@pytest.mark.notebook_test
def test_add_pipeline():
    with exec_for_test(
        "add_pipeline", {"loggers": {"console": {"config": {"log_level": "ERROR"}}}}
    ) as result:
        assert result.success
        assert result.result_for_solid("add_two_numbers").output_value() == 3


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
    with pytest.raises(PapermillExecutionError) as exc:
        with exec_for_test("error_pipeline") as result:
            pass

    assert "Someone set up us the bomb" in str(exc.value)

    with exec_for_test("error_pipeline", raise_on_error=False) as result:
        assert not result.success
        assert result.step_event_list[1].event_type.value == "STEP_MATERIALIZATION"
        assert result.step_event_list[2].event_type.value == "STEP_FAILURE"


@pytest.mark.nettest
@pytest.mark.notebook_test
@pytest.mark.skipif(
    not (DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT),
    reason="tutorial_pipeline reqs not present: dagster_pandas, sklearn, matplotlib",
)
def test_tutorial_pipeline():
    with exec_for_test(
        "tutorial_pipeline", {"loggers": {"console": {"config": {"log_level": "DEBUG"}}}}
    ) as result:
        assert result.success


@pytest.mark.notebook_test
def test_hello_world_reexecution():
    with exec_for_test("hello_world_pipeline") as result:
        assert result.success

        output_notebook_path = get_path(
            [x for x in result.step_event_list if x.event_type_value == "STEP_MATERIALIZATION"][0]
        )

        with tempfile.NamedTemporaryFile("w+", suffix=".py") as reexecution_notebook_file:
            reexecution_notebook_file.write(
                (
                    "from dagster import pipeline\n"
                    "from dagstermill import define_dagstermill_solid\n\n\n"
                    "reexecution_solid = define_dagstermill_solid(\n"
                    "    'hello_world_reexecution', '{output_notebook_path}'\n"
                    ")\n\n"
                    "@pipeline\n"
                    "def reexecution_pipeline():\n"
                    "    reexecution_solid()\n"
                ).format(output_notebook_path=output_notebook_path)
            )
            reexecution_notebook_file.flush()

            result = None
            reexecution_pipeline = ReconstructablePipeline.for_file(
                reexecution_notebook_file.name, "reexecution_pipeline"
            )

            reexecution_result = None
            with instance_for_test() as instance:
                try:
                    reexecution_result = execute_pipeline(reexecution_pipeline, instance=instance)
                    assert reexecution_result.success
                finally:
                    if reexecution_result:
                        cleanup_result_notebook(reexecution_result)


@pytest.mark.notebook_test
def test_resources_notebook():
    with safe_tempfile_path() as path:
        with exec_for_test(
            "resource_pipeline",
            {"resources": {"list": {"config": path}}},
            mode="prod",
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
                "raise Exception()" in result.step_event_list[8].event_specific_data.error.message
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
def test_bad_kernel_pipeline():
    with pytest.raises(NoSuchKernel):
        with exec_for_test("bad_kernel_pipeline"):
            pass


@pytest.mark.notebook_test
def test_hello_logging():
    with exec_for_test("hello_logging_pipeline") as result:
        assert result.success


@pytest.mark.notebook_test
def test_reimport():
    with exec_for_test("reimport_pipeline") as result:
        assert result.success
        assert result.result_for_solid("reimport").output_value() == 6


@pytest.mark.notebook_test
def test_yield_3_pipeline():
    with exec_for_test("yield_3_pipeline") as result:
        assert result.success
        assert result.result_for_solid("yield_3").output_value() == 3


@pytest.mark.notebook_test
def test_yield_obj_pipeline():
    with exec_for_test("yield_obj_pipeline") as result:
        assert result.success
        assert result.result_for_solid("yield_obj").output_value().x == 3


@pytest.mark.notebook_test
def test_hello_world_with_custom_tags_and_description_pipeline():
    with exec_for_test("hello_world_with_custom_tags_and_description_pipeline") as result:
        assert result.success


def test_non_reconstructable_pipeline():
    foo_solid = define_dagstermill_solid("foo", file_relative_path(__file__, "notebooks/foo.ipynb"))

    @pipeline
    def non_reconstructable():
        foo_solid()

    with pytest.raises(DagstermillError, match="pipeline that is not reconstructable."):
        execute_pipeline(non_reconstructable)


# Test Solid Tags & Description

BACKING_NB_NAME = "hello_world"
BACKING_NB_PATH = file_relative_path(__file__, f"notebooks/{BACKING_NB_NAME}.ipynb")


def test_default_tags():
    test_solid_default_tags = define_dagstermill_solid(BACKING_NB_NAME, BACKING_NB_PATH)

    assert test_solid_default_tags.tags == {
        "kind": "ipynb",
        "notebook_path": BACKING_NB_PATH,
    }


def test_custom_tags():
    test_solid_custom_tags = define_dagstermill_solid(
        BACKING_NB_NAME, BACKING_NB_PATH, tags={"foo": "bar"}
    )

    assert test_solid_custom_tags.tags == {
        "kind": "ipynb",
        "notebook_path": BACKING_NB_PATH,
        "foo": "bar",
    }


def test_reserved_tags_not_overridden():
    with pytest.raises(CheckError, match="key is reserved for use by Dagster"):
        define_dagstermill_solid(BACKING_NB_NAME, BACKING_NB_PATH, tags={"notebook_path": "~"})

    with pytest.raises(CheckError, match="key is reserved for use by Dagster"):
        define_dagstermill_solid(BACKING_NB_NAME, BACKING_NB_PATH, tags={"kind": "py"})


def test_default_description():
    test_solid = define_dagstermill_solid(BACKING_NB_NAME, BACKING_NB_PATH)
    assert test_solid.description.startswith("This solid is backed by the notebook at ")


def test_custom_description():
    test_description = "custom description"
    test_solid = define_dagstermill_solid(
        BACKING_NB_NAME, BACKING_NB_PATH, description=test_description
    )
    assert test_solid.description == test_description
