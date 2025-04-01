"""Unit testing the Mlflow class."""

import logging
import random
import string
import uuid
from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock, patch

import mlflow
import pandas as pd
import pytest
from dagster import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster_mlflow.resources import MlFlow, mlflow_tracking
from mlflow.exceptions import MlflowException


@pytest.fixture
def string_maker():
    class Dummy:
        def __call__(self, size=5):
            return "".join(random.choice(string.ascii_letters) for _ in range(size))

    return Dummy()


@pytest.fixture
def basic_run_config() -> Mapping[str, Any]:
    return {
        "resources": {"mlflow": {"config": {"experiment_name": "testing"}}},
        "ops": {},
    }


@pytest.fixture
def mlflow_run_config(basic_run_config):
    config = deepcopy(basic_run_config)
    config["resources"]["mlflow"]["config"]["env"] = {
        "what": "do we do with the drunken sailor?",
        "early": "in the morning",
        "put": "tag",
    }
    config["resources"]["mlflow"]["config"]["env_to_tag"] = ["what", "put"]
    return config


@pytest.fixture
def multiprocess_mlflow_run_config(mlflow_run_config):
    config = deepcopy(mlflow_run_config)
    config["execution"] = {"multiprocess": {"config": {"max_concurrent": 2}}}
    return config


@pytest.fixture(params=["basic_context", "child_context"])
def context(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def dagster_run():
    return MagicMock(job_name="test")


@pytest.fixture
def basic_context(mlflow_run_config, dagster_run):
    return MagicMock(
        resource_config=mlflow_run_config["resources"]["mlflow"]["config"],
        log=logging.getLogger(),
        run_id=str(uuid.uuid4()),
        job_run=dagster_run,
    )


@pytest.fixture
def child_context(basic_context, mlflow_run_config):
    resource_config = deepcopy(mlflow_run_config["resources"]["mlflow"]["config"])
    resource_config["parent_run_id"] = basic_context.run_id
    return MagicMock(
        resource_config=resource_config,
        log=basic_context.log,
        run_id=str(uuid.uuid4()),
        dagster_run=basic_context.dagster_ryn,
        extra_tags={"wala": "lala"},
    )


@pytest.fixture
def cleanup_mlflow_runs():
    yield
    while mlflow.active_run():
        mlflow.end_run()


@patch("os.environ.update")
@patch("mlflow.set_tracking_uri")
@patch("mlflow.get_experiment_by_name")
@patch("mlflow.set_experiment")
@patch("mlflow.tracking.MlflowClient")
def test_mlflow_constructor_basic(
    mock_mlflowclient,
    mock_set_experiment,
    mock_get_experiment_by_name,
    mock_set_tracking_uri,
    mock_environ_update,
    context,
):
    with patch.object(MlFlow, "_setup") as mock_setup:
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)
        # Then:
        # the _setup() is called once
        mock_setup.assert_called_once()
    # - the mlflow library methods & attributes have been added to the object
    assert all(hasattr(mlf, attr) for attr in dir(MlFlow) if attr not in ("__name__"))

    # - the context associated attributes passed have been set
    assert mlf.log == context.log
    assert mlf.run_name == context.dagster_run.job_name
    assert mlf.dagster_run_id == context.run_id

    # - the tracking URI is the same as what was passed
    assert mlf.tracking_uri == context.resource_config.get("mlflow_tracking_uri")
    # - the tracking URI was set to mlflow
    if mlf.tracking_uri:
        mock_set_tracking_uri.assert_called_once_with(mlf.tracking_uri)
    else:
        mock_set_tracking_uri.assert_not_called()
    # - the resource config attributes have been set
    assert mlf.parent_run_id == context.resource_config.get("parent_run_id")
    assert mlf.experiment_name == context.resource_config.get("experiment_name")
    assert mlf.env_tags_to_log == context.resource_config.get("env_to_tag", [])
    assert mlf.extra_tags == context.resource_config.get("extra_tags")
    assert mlf.env_vars == context.resource_config.get("env", {})

    # - the env vars that have been updated are set
    if mlf.env_vars:
        mock_environ_update.assert_called_once_with(mlf.env_vars)
    else:
        mock_environ_update.assert_not_called()
    mock_set_experiment.assert_called_once_with(mlf.experiment_name)
    mock_get_experiment_by_name(mlf.experiment_name)
    # - mlflow.tracking.MlflowClient has been called
    mock_mlflowclient.assert_called_once()


def test_mlflow_meta_not_overloading():
    # Given an MlFlow
    # And: a list of overloaded mlflow methods
    # TODO: find a way to get this list
    over_list = ["log_params"]
    for methods in over_list:
        # then: the function signature is not the same as the mlflow one
        assert getattr(MlFlow, methods) != getattr(mlflow, methods)


def test_mlflow_meta_overloading():
    # Given an MlFlow
    # And: a list of inherited mlflow methods
    # TODO: find a way to get this list
    inherited_list = [
        method for method in dir(mlflow) if method not in ["log_params", "__name__", "__doc__"]
    ]

    for methods in inherited_list:
        assert getattr(MlFlow, methods) == getattr(mlflow, methods)


@patch("mlflow.start_run")
def test_start_run(mock_start_run, context):
    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)

    # When: a run is started
    run_id_1 = str(uuid.uuid4())
    mlf._start_run(run_id=run_id_1)  # noqa: SLF001
    # Then mlflow start_run is called
    mock_start_run.assert_called_once_with(run_id=run_id_1)

    # And when start run is called with the same run_id no excpetion is raised
    mlf._start_run(run_id=run_id_1)  # noqa: SLF001


@patch("mlflow.end_run")
@pytest.mark.parametrize("any_error", [KeyboardInterrupt(), OSError(), RuntimeError(), None])
def test_cleanup_on_error(
    mock_mlflow_end_run,
    any_error,
    context,
    cleanup_mlflow_runs,
):
    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)
    # When: a run is started
    mlf.start_run()  # pyright: ignore[reportAttributeAccessIssue]

    with patch("sys.exc_info", return_value=[0, any_error]):
        # When: cleanup_on_error is called
        mlf.cleanup_on_error()
    # Then:
    if any_error:
        if isinstance(any_error, KeyboardInterrupt):
            # mlflow.end_run is called with status=KILLED if KeyboardInterrupt
            mock_mlflow_end_run.assert_called_once_with(status="KILLED")
        else:
            # mlflow.end_run is called with status=FAILED for all other errors
            mock_mlflow_end_run.assert_called_once_with(status="FAILED")
        assert True
    else:
        # mlflow.end_run is not called when no error is flagged
        mock_mlflow_end_run.assert_not_called()


@patch("mlflow.set_tags")
def test_set_all_tags(mock_mlflow_set_tags, context):
    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)
    # When all the tags are set
    mlf._set_all_tags()  # noqa: SLF001

    # Given: the tags that should be set in mlflow
    tags = {
        tag: context.resource_config["env"][tag] for tag in context.resource_config["env_to_tag"]
    }
    tags["dagster_run_id"] = mlf.dagster_run_id
    if mlf.extra_tags:
        tags.update(mlf.extra_tags)
    # Then the Mlflow.set_tags is called with the set tags
    mock_mlflow_set_tags.assert_called_once_with(tags)


@pytest.mark.parametrize("run_df", [pd.DataFrame(), pd.DataFrame(data={"run_id": ["100"]})])
@pytest.mark.parametrize(
    "experiment", [None, MagicMock(experiment_id="1"), MagicMock(experiment_id="lol")]
)
def test_get_current_run_id(context, experiment, run_df):
    with patch.object(MlFlow, "_setup"):
        # Given: an initialization of the mlflow object
        mlf = MlFlow(context)

    with patch("mlflow.search_runs", return_value=run_df):
        # when: _get_current_run_id is called
        run_id = mlf._get_current_run_id(experiment=experiment)  # noqa: SLF001
    # Then: the run_id id provided is the same as what was provided
    if not run_df.empty:
        assert run_id == run_df.run_id.values[0]
    else:
        assert run_id is None


def test_get_current_run_id_with_one_mlflow_error(context):
    experiment = MagicMock(experiment_id="1")
    run_df = pd.DataFrame(data={"run_id": ["100"]})

    with patch.object(MlFlow, "_setup"):
        # Given: an initialization of the mlflow object
        mlf = MlFlow(context)

    # Simulate MlflowException being raised once, then return the run_df
    with patch(
        "mlflow.search_runs",
        side_effect=[
            MlflowException(
                "Max retries exceeded with url: /api/2.0/mlflow/runs/search (Caused by ResponseError('too many 429 error "
                "responses')"
            ),
            run_df,
        ],
    ):
        # when: _get_current_run_id is called
        run_id = mlf._get_current_run_id(experiment=experiment)  # noqa: SLF001

    # Then: the run_id id provided is the same as what was provided
    assert run_id == run_df.run_id.values[0]


@patch("atexit.unregister")
def test_setup(mock_atexit, context):
    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)

    with (
        patch.object(
            MlFlow, "_get_current_run_id", return_value="run_id_mock"
        ) as mock_get_current_run_id,
        patch.object(MlFlow, "_set_active_run") as mock_set_active_run,
        patch.object(MlFlow, "_set_all_tags") as mock_set_all_tags,
    ):
        # When _setup is called
        mlf._setup()  # noqa: SLF001
        # Then
        # - _get_current_run_id is called once with the experiment object
        mock_get_current_run_id.assert_called()
        # - _set_active_run is called once with the run_id returned from _get_current_run_id
        mock_set_active_run.assert_called_once_with(run_id="run_id_mock")
        # - _set_all_tags is called once
        mock_set_all_tags.assert_called_once()
    # - atexit.unregister is called with mlf.end_run as an argument
    mock_atexit.assert_called_once_with(mlf.end_run)  # pyright: ignore[reportAttributeAccessIssue]


@patch("atexit.unregister")
def test_setup_with_passed_run_id(mock_atexit, context):
    # Given: a mlflow_run_id of zero
    context.resource_config["mlflow_run_id"] = 0

    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)

    with (
        patch.object(
            MlFlow, "_get_current_run_id", return_value="run_id_mock"
        ) as mock_get_current_run_id,
        patch.object(MlFlow, "_set_active_run") as mock_set_active_run,
        patch.object(MlFlow, "_set_all_tags") as mock_set_all_tags,
    ):
        # When _setup is called
        mlf._setup()  # noqa: SLF001
        # Then
        # - _get_current_run_id is called once with the experiment object
        mock_get_current_run_id.assert_not_called()
        # - _set_active_run is called once with the run_id returned from _get_current_run_id
        mock_set_active_run.assert_called_once_with(run_id=0)
        # - _set_all_tags is called once
        mock_set_all_tags.assert_called_once()
    # - atexit.unregister is called with mlf.end_run as an argument
    mock_atexit.assert_called_once_with(mlf.end_run)  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("run_id", [None, 0, "12"])
def test_set_active_run(context, run_id):
    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(context)

    with patch.object(MlFlow, "_start_run") as mock_start_run:
        # When _set_active_run is called
        mlf._set_active_run(run_id=run_id)  # noqa: SLF001

    # And: the run is nested
    if mlf.parent_run_id is not None:
        # Then:
        # - the parent run is started if required
        mock_start_run.assert_any_call(run_id=mlf.parent_run_id, run_name=mlf.run_name)
        # - mlflow.start_run is called with nested=True
        mock_start_run.assert_any_call(run_id=run_id, run_name=mlf.run_name, nested=True)
        # - _start_run is called twice
        assert mock_start_run.call_count == 2
    # And: the run is not nested
    else:
        # Then:
        mock_start_run.assert_called_once_with(run_id=run_id, run_name=mlf.run_name, nested=False)


def test_set_active_run_parent_zero(child_context):
    # Given: a parent_run_id of zero
    child_context.resource_config["parent_run_id"] = 0
    with patch.object(MlFlow, "_setup"):
        # Given: a context  passed into the __init__ for MlFlow
        mlf = MlFlow(child_context)

    with patch.object(MlFlow, "_start_run") as mock_start_run:
        # And _set_active_run is called with run_id
        mlf._set_active_run(run_id="what-is-an-edge-case")  # noqa: SLF001
        # Then: _start_run_by_id is called with the parent_id
        mock_start_run.assert_any_call(run_id=mlf.parent_run_id, run_name=mlf.run_name)
        # And: mlflow.start_run is called with the run_name and nested=True
        mock_start_run.assert_any_call(
            run_id="what-is-an-edge-case", run_name=mlf.run_name, nested=True
        )
        # And _start_run is called twice
        assert mock_start_run.call_count == 2


@patch("mlflow.log_params")
@pytest.mark.parametrize("num_of_params", (90, 101, 223))
def test_log_params(mock_log_params, context, num_of_params, string_maker):
    # Given: init of MlFlow
    with patch.object(MlFlow, "_setup"):
        mlf = MlFlow(context)
    # And: a set of parameters
    param = {string_maker(5): string_maker(5) for _ in range(num_of_params)}
    # When: log_params is called
    mlf.log_params(param)
    # Then mock_log_params is called the correct number of times
    assert mock_log_params.call_count == num_of_params // 100 + (1 if num_of_params % 100 else 0)


@pytest.mark.parametrize("chunk", (10, 100))
@pytest.mark.parametrize("num_of_params", (90, 200))
def test_chunks(context, num_of_params, string_maker, chunk):
    # Given: init of MLFlow
    with patch.object(MlFlow, "_setup"):
        mlf = MlFlow(context)
    # And: a dictionary
    D = {string_maker(5): string_maker(5) for _ in range(num_of_params)}
    # When: dictionary is chunked
    param_chunks_list = [param_chunk for param_chunk in mlf.chunks(D, chunk)]

    # Then
    # - the number of chunks is what is expected
    assert len(param_chunks_list) == num_of_params // chunk + (1 if num_of_params % chunk else 0)
    # - the unwrapped dictionary is the same as was set
    assert {k: v for d in param_chunks_list for k, v in d.items()} == D


def test_execute_op_with_mlflow_resource():
    run_id_holder = {}

    params = {"learning_rate": "0.01", "n_estimators": "10"}
    extra_tags = {"super": "experiment"}

    @op(required_resource_keys={"mlflow"})
    def op1(_):
        mlflow.log_params(params)
        run_id_holder["op1_run_id"] = mlflow.active_run().info.run_id

    @op(required_resource_keys={"mlflow"})
    def op2(_, _arg1):
        run_id_holder["op2_run_id"] = mlflow.active_run().info.run_id

    @job(resource_defs={"mlflow": mlflow_tracking})
    def mlf_job():
        op2(op1())

    result = mlf_job.execute_in_process(
        run_config={
            "resources": {
                "mlflow": {
                    "config": {
                        "experiment_name": "my_experiment",
                        "extra_tags": extra_tags,
                    }
                }
            }
        },
    )
    assert result.success

    assert run_id_holder["op1_run_id"] == run_id_holder["op2_run_id"]
    run = mlflow.get_run(run_id_holder["op1_run_id"])
    assert run.data.params == params
    assert set(extra_tags.items()).issubset(run.data.tags.items())

    assert mlflow.get_experiment_by_name("my_experiment")
