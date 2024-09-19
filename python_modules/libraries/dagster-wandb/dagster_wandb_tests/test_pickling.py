from unittest.mock import ANY, MagicMock, patch

import pytest
from dagster import build_output_context
from dagster_wandb.utils.pickling import pickle_artifact_content


@pytest.fixture
def pickle_dump_mock():
    with patch("pickle.dump") as mock:
        yield mock


@pytest.fixture
def dill_dump_mock():
    with patch("dill.dump") as mock:
        yield mock


@pytest.fixture
def cloudpickle_dump_mock():
    with patch("cloudpickle.dump") as mock:
        yield mock


@pytest.fixture
def joblib_dump_mock():
    with patch("joblib.dump") as mock:
        yield mock


@pytest.fixture
def artifact_mock():
    mocked_artifact = MagicMock()

    with patch("wandb.Artifact", autospec=True, return_value=mocked_artifact) as mock:
        yield mock


def test_pickle_artifact_content_with_pickle_protocol(artifact_mock, pickle_dump_mock):
    context = build_output_context()
    output_value = "content"
    pickle_artifact_content(
        context, "pickle", {"protocol": 5}, artifact_mock.return_value, output_value
    )

    assert artifact_mock.return_value.metadata == {
        "source_pickle_protocol_used": ANY,
        "source_serialization_module": "pickle",
    }
    assert artifact_mock.return_value.new_file.call_count == 1
    artifact_mock.return_value.new_file.assert_called_with("output.pickle", "wb")
    assert pickle_dump_mock.call_count == 1
    pickle_dump_mock.assert_called_with(
        output_value,
        artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
        protocol=ANY,
    )


def test_pickle_artifact_content_with_dill_protocol(artifact_mock, dill_dump_mock):
    context = build_output_context()
    output_value = "content"
    pickle_artifact_content(
        context, "dill", {"protocol": 5}, artifact_mock.return_value, output_value
    )

    assert artifact_mock.return_value.metadata == {
        "source_pickle_protocol_used": ANY,
        "source_dill_version_used": ANY,
        "source_serialization_module": "dill",
    }
    assert artifact_mock.return_value.new_file.call_count == 1
    artifact_mock.return_value.new_file.assert_called_with("output.dill", "wb")
    assert dill_dump_mock.call_count == 1
    dill_dump_mock.assert_called_with(
        output_value,
        artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
        protocol=ANY,
    )


def test_pickle_artifact_content_with_cloudpickle_protocol(artifact_mock, cloudpickle_dump_mock):
    context = build_output_context()
    output_value = "content"
    pickle_artifact_content(
        context, "cloudpickle", {"protocol": 5}, artifact_mock.return_value, output_value
    )

    assert artifact_mock.return_value.metadata == {
        "source_pickle_protocol_used": ANY,
        "source_cloudpickle_version_used": ANY,
        "source_serialization_module": "cloudpickle",
    }
    assert artifact_mock.return_value.new_file.call_count == 1
    artifact_mock.return_value.new_file.assert_called_with("output.cloudpickle", "wb")
    assert cloudpickle_dump_mock.call_count == 1
    cloudpickle_dump_mock.assert_called_with(
        output_value,
        artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
        protocol=ANY,
    )


def test_pickle_artifact_content_with_joblib_protocol(artifact_mock, joblib_dump_mock):
    context = build_output_context()
    output_value = "content"
    pickle_artifact_content(
        context, "joblib", {"protocol": 5}, artifact_mock.return_value, output_value
    )

    assert artifact_mock.return_value.metadata == {
        "source_pickle_protocol_used": ANY,
        "source_joblib_version_used": ANY,
        "source_serialization_module": "joblib",
    }
    assert artifact_mock.return_value.new_file.call_count == 1
    artifact_mock.return_value.new_file.assert_called_with("output.joblib", "wb")
    assert joblib_dump_mock.call_count == 1
    joblib_dump_mock.assert_called_with(
        output_value,
        artifact_mock.return_value.new_file.return_value.__enter__.return_value,  # new_file Context Manager
        protocol=ANY,
    )
