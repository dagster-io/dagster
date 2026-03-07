import orjson
import pytest

from dagster_dbt.utils import _select_unique_ids_from_cli


def _mock_invocation(mocker):
    mock_dbt_cli_resource_class = mocker.patch("dagster_dbt.utils.DbtCliResource")
    mock_dbt_cli_resource = mock_dbt_cli_resource_class.return_value
    mock_invocation = mock_dbt_cli_resource.cli.return_value
    return mock_dbt_cli_resource, mock_invocation


def test_select_unique_ids_from_cli_success(mocker):
    mock_dbt_cli_resource, mock_invocation = _mock_invocation(mocker)

    mock_invocation._stream_stdout.return_value = [
        {"info": {"msg": orjson.dumps({"unique_id": "model.my_project.my_model"}).decode()}},
        {"info": {"msg": orjson.dumps({"unique_id": "model.my_project.another_model"}).decode()}},
        {"info": {"msg": orjson.dumps({"unique_id": None}).decode()}},
        {"info": {"msg": "random non-json log"}},
        "string log",
    ]
    mock_invocation.is_successful.return_value = True

    unique_ids = _select_unique_ids_from_cli("my_model", "", "", "fake_project")
    assert unique_ids == {"model.my_project.my_model", "model.my_project.another_model"}

    mock_dbt_cli_resource.cli.assert_called_once()
    mock_invocation._stream_stdout.assert_called_once()
    mock_invocation.is_successful.assert_called_once()
    mock_invocation.get_error.assert_not_called()


def test_select_unique_ids_from_cli_success_empty_events(mocker):
    mock_dbt_cli_resource, mock_invocation = _mock_invocation(mocker)

    mock_invocation._stream_stdout.return_value = [
        {"info": {"msg": "{}"}},         # valid json but no unique_id
        {"info": {"msg": ""}},           # invalid json
        {"info": {"msg": "not json"}},   # invalid json
        {},                              # missing info/msg
        "string log",
    ]
    mock_invocation.is_successful.return_value = True

    unique_ids = _select_unique_ids_from_cli("my_model", "", "", "fake_project")
    assert unique_ids == set()

    mock_dbt_cli_resource.cli.assert_called_once()
    mock_invocation._stream_stdout.assert_called_once()
    mock_invocation.is_successful.assert_called_once()
    mock_invocation.get_error.assert_not_called()


def test_select_unique_ids_from_cli_failure_with_error(mocker):
    mock_dbt_cli_resource, mock_invocation = _mock_invocation(mocker)

    mock_invocation._stream_stdout.return_value = []
    mock_invocation.is_successful.return_value = False
    err = RuntimeError("dbt invocation failed explicitly")
    mock_invocation.get_error.return_value = err

    with pytest.raises(RuntimeError) as e:
        _select_unique_ids_from_cli("my_model", "", "", "fake_project")
    assert e.value is err

    mock_dbt_cli_resource.cli.assert_called_once()
    mock_invocation._stream_stdout.assert_called_once()
    mock_invocation.is_successful.assert_called_once()
    mock_invocation.get_error.assert_called_once()


def test_select_unique_ids_from_cli_failure_without_error(mocker):
    mock_dbt_cli_resource, mock_invocation = _mock_invocation(mocker)

    mock_invocation._stream_stdout.return_value = []
    mock_invocation.is_successful.return_value = False
    mock_invocation.get_error.return_value = None

    with pytest.raises(RuntimeError, match="dbt invocation failed but no error was captured"):
        _select_unique_ids_from_cli("my_model", "", "", "fake_project")

    mock_dbt_cli_resource.cli.assert_called_once()
    mock_invocation._stream_stdout.assert_called_once()
    mock_invocation.is_successful.assert_called_once()
    mock_invocation.get_error.assert_called_once()