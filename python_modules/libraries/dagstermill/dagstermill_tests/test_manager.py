import contextlib
import os
import pickle
import shutil
import tempfile
import threading

import dagstermill
import pytest
from dagster import AssetMaterialization, ModeDefinition, ResourceDefinition, check
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.test_utils import instance_for_test
from dagster.core.utils import make_new_run_id
from dagster.serdes import pack_value
from dagster.utils import safe_tempfile_path
from dagstermill import DagstermillError
from dagstermill.manager import Manager


@contextlib.contextmanager
def in_pipeline_manager(
    pipeline_name="hello_world_pipeline",
    solid_handle=SolidHandle("hello_world", None),
    executable_dict=None,
    mode=None,
    **kwargs,
):
    manager = Manager()

    run_id = make_new_run_id()
    with instance_for_test() as instance:
        marshal_dir = tempfile.mkdtemp()

        if not executable_dict:
            executable_dict = ReconstructablePipeline.for_module(
                "dagstermill.examples.repository", "hello_world_pipeline"
            ).to_dict()

        pipeline_run_dict = pack_value(
            PipelineRun(
                pipeline_name=pipeline_name,
                run_id=run_id,
                mode=mode or "default",
                run_config=None,
                step_keys_to_execute=None,
                status=PipelineRunStatus.NOT_STARTED,
            )
        )

        try:
            with safe_tempfile_path() as output_log_file_path:
                context_dict = {
                    "pipeline_run_dict": pipeline_run_dict,
                    "solid_handle_kwargs": solid_handle._asdict(),
                    "executable_dict": executable_dict,
                    "marshal_dir": marshal_dir,
                    "run_config": {},
                    "output_log_path": output_log_file_path,
                    "instance_ref_dict": pack_value(instance.get_ref()),
                }

                manager.reconstitute_pipeline_context(**dict(context_dict, **kwargs))
                yield manager
        finally:
            shutil.rmtree(marshal_dir)


def test_get_out_of_pipeline_context():
    context = dagstermill.get_context(
        mode_def=ModeDefinition(resource_defs={"list": ResourceDefinition(lambda _: [])})
    )

    assert context.pipeline_name == "ephemeral_dagstermill_pipeline"
    assert context.resources.list == []


def test_get_out_of_pipeline_solid_config():
    assert dagstermill.get_context(solid_config="bar").solid_config == "bar"


def test_out_of_pipeline_manager_yield_result():
    manager = Manager()
    assert manager.yield_result("foo") == "foo"


def test_out_of_pipeline_manager_yield_complex_result():
    class Foo:
        pass

    manager = Manager()
    assert isinstance(manager.yield_result(Foo()), Foo)


def test_in_pipeline_manager_yield_bad_result():
    with in_pipeline_manager() as manager:
        with pytest.raises(
            DagstermillError, match="Solid hello_world does not have output named result"
        ):
            assert manager.yield_result("foo") == "foo"


def test_yield_unserializable_result():
    manager = Manager()
    assert manager.yield_result(threading.Lock())

    with in_pipeline_manager(
        pipeline_name="hello_world_output_pipeline",
        solid_handle=SolidHandle("hello_world_output", None),
        executable_dict=ReconstructablePipeline.for_module(
            "dagstermill.examples.repository",
            "hello_world_output_pipeline",
        ).to_dict(),
    ) as manager:
        with pytest.raises(TypeError):
            manager.yield_result(threading.Lock())


def test_in_pipeline_manager_bad_solid():
    with pytest.raises(
        check.CheckError,
        match=("hello_world_pipeline has no solid named foobar"),
    ):
        with in_pipeline_manager(solid_handle=SolidHandle("foobar", None)) as _manager:
            pass


def test_in_pipeline_manager_bad_yield_result():
    with in_pipeline_manager() as manager:
        with pytest.raises(
            DagstermillError, match="Solid hello_world does not have output named result"
        ):
            manager.yield_result("foo")


def test_out_of_pipeline_yield_event():
    manager = Manager()
    assert manager.yield_event(AssetMaterialization("foo")) == AssetMaterialization("foo")


def test_in_pipeline_manager_resources():
    with in_pipeline_manager() as manager:
        assert "file_manager" in manager.context.resources._asdict()
        assert "io_manager" in manager.context.resources._asdict()
        assert len(manager.context.resources._asdict()) == 2


def test_in_pipeline_manager_solid_config():
    with in_pipeline_manager() as manager:
        assert manager.context.solid_config is None

    with in_pipeline_manager(
        pipeline_name="hello_world_config_pipeline",
        solid_handle=SolidHandle("hello_world_config", None),
        executable_dict=ReconstructablePipeline.for_module(
            "dagstermill.examples.repository",
            "hello_world_config_pipeline",
        ).to_dict(),
    ) as manager:
        assert manager.context.solid_config == {"greeting": "hello"}

    with in_pipeline_manager(
        pipeline_name="hello_world_config_pipeline",
        solid_handle=SolidHandle("hello_world_config", None),
        run_config={
            "solids": {
                "hello_world_config": {"config": {"greeting": "bonjour"}},
                "goodbye_config": {"config": {"farewell": "goodbye"}},
            }
        },
        executable_dict=ReconstructablePipeline.for_module(
            "dagstermill.examples.repository",
            "hello_world_config_pipeline",
        ).to_dict(),
    ) as manager:
        assert manager.context.solid_config == {"greeting": "bonjour"}

    with in_pipeline_manager(
        pipeline_name="hello_world_config_pipeline",
        solid_handle=SolidHandle("goodbye_config", None),
        run_config={
            "solids": {
                "hello_world_config": {
                    "config": {"greeting": "bonjour"},
                },
                "goodbye_config": {"config": {"farewell": "goodbye"}},
            }
        },
        executable_dict=ReconstructablePipeline.for_module(
            "dagstermill.examples.repository",
            "hello_world_config_pipeline",
        ).to_dict(),
    ) as manager:
        assert manager.context.solid_config == {"farewell": "goodbye"}


def test_in_pipeline_manager_with_resources():
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        with in_pipeline_manager(
            pipeline_name="resource_pipeline",
            executable_dict=ReconstructablePipeline.for_module(
                "dagstermill.examples.repository",
                "resource_pipeline",
            ).to_dict(),
            solid_handle=SolidHandle("hello_world_resource", None),
            run_config={"resources": {"list": {"config": path}}},
            mode="prod",
        ) as manager:
            assert "list" in manager.context.resources._asdict()

            with open(path, "rb") as fd:
                messages = pickle.load(fd)

            messages = [message.split(": ") for message in messages]

            assert len(messages) == 1
            assert messages[0][1] == "Opened"

            manager.teardown_resources()

            with open(path, "rb") as fd:
                messages = pickle.load(fd)

            messages = [message.split(": ") for message in messages]

            assert len(messages) == 2
            assert messages[1][1] == "Closed"

    finally:
        if os.path.exists(path):
            os.unlink(path)
