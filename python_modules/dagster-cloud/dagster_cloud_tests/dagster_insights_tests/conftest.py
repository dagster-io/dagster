import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import pytest
from dagster_dbt import DbtCliResource
from google.api_core.exceptions import NotFound
from google.cloud.bigquery import DatasetReference

JAFFLE_SHOP_ASSET_KEYS = {
    "customers",
    "orders",
    "raw_customers",
    "raw_orders",
    "raw_payments",
    "stg_customers",
    "stg_orders",
    "stg_payments",
}


@dataclass
class BigqueryCostRow:
    job_id: str
    unique_id: str
    bytes_billed: int
    slots_ms: int


@pytest.fixture(scope="session")
def snowflake_jaffle_dir():
    yield Path(__file__).parent / "snowflake_jaffle"


@pytest.fixture(scope="session")
def snowflake_manifest_path(snowflake_jaffle_dir):
    dbt = DbtCliResource(project_dir=os.fspath(snowflake_jaffle_dir))
    dbt.cli(["deps"]).wait()
    dbt_parse_invocation = dbt.cli(["parse"]).wait()
    snowflake_manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
    yield snowflake_manifest_path


@pytest.fixture(scope="session")
def bigquery_jaffle_dir():
    yield Path(__file__).parent / "bigquery_jaffle"


@pytest.fixture(scope="session")
def bigquery_manifest_path(bigquery_jaffle_dir):
    dbt = DbtCliResource(project_dir=os.fspath(bigquery_jaffle_dir))
    dbt.cli(["deps"]).wait()
    dbt_parse_invocation = dbt.cli(["parse"]).wait()
    manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
    yield manifest_path


@contextmanager
def bigquery_client(
    client_location: str | None = None,
    client_project: str | None = None,
    dataset_location: str | None = None,
    dataset_project: str | None = None,
):
    with mock.patch(
        "dbt.adapters.contracts.connection.Connection.handle",
        new_callable=mock.PropertyMock,
    ) as mock_get_client:
        mock_dataset = mock.MagicMock()
        mock_dataset.location = dataset_location
        mock_dataset.project = dataset_project
        mock_client = mock.MagicMock()
        mock_client.get_dataset.return_value = mock_dataset
        mock_client.query.return_value = _fake_cost_rows()
        mock_client.location = client_location
        mock_client.project = client_project
        mock_get_client.return_value = mock_client
        yield mock_client


def _fake_cost_rows():
    rows = []
    for idx, asset_key_string in enumerate(JAFFLE_SHOP_ASSET_KEYS):
        unique_id = (
            f"seed.jaffle_shop.{asset_key_string}"
            if asset_key_string.startswith("raw_")
            else f"model.jaffle_shop.{asset_key_string}"
        )
        # make sure we have a mix of non-null and null values for bytes_billed and slot_ms
        if idx % 3 == 0:
            bytes_billed = 1000
            slot_ms = 1
        elif idx % 3 == 1:
            bytes_billed = None
            slot_ms = 1
        else:
            bytes_billed = 1000
            slot_ms = None
        rows.append(BigqueryCostRow("fake_job_id", unique_id, bytes_billed, slot_ms))  # ty: ignore[invalid-argument-type]
    return rows


@pytest.fixture
def default_bigquery_client():
    with bigquery_client("US", "fake_project") as client:
        yield client


@pytest.fixture(scope="session")
def bigquery_with_check_failure_jaffle_dir():
    yield Path(__file__).parent / "bigquery_jaffle_with_check_failure"


@pytest.fixture(scope="session")
def bigquery_with_check_failure_manifest_path(bigquery_with_check_failure_jaffle_dir):
    dbt = DbtCliResource(project_dir=os.fspath(bigquery_with_check_failure_jaffle_dir))
    dbt.cli(["deps"]).wait()
    dbt_parse_invocation = dbt.cli(["parse"]).wait()
    manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
    yield manifest_path


def get_dataset_side_effect(dataset_ref):
    if isinstance(dataset_ref, DatasetReference) and dataset_ref.project == "fake_default_project":
        mock_dataset = mock.MagicMock()
        mock_dataset.location = "US"
        mock_dataset.project = "fake_default_project"
        return mock_dataset
    else:
        raise NotFound("Dataset not found")


def create_dataset_ref_side_effect(schema, project):
    return DatasetReference(project, schema)


@pytest.fixture
def bigquery_client_with_execution_project():
    with mock.patch(
        "dbt.adapters.contracts.connection.Connection.handle",
        new_callable=mock.PropertyMock,
    ) as mock_get_client:
        mock_client = mock.MagicMock()
        mock_client.get_dataset = mock.MagicMock(side_effect=get_dataset_side_effect)
        mock_client.query.return_value = _fake_cost_rows()
        mock_client.location = None
        mock_client.project = "fake_exec_project"
        mock_client.dataset = mock.MagicMock(side_effect=create_dataset_ref_side_effect)
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="session")
def bigquery_with_execution_project_jaffle_dir():
    yield Path(__file__).parent / "bigquery_jaffle_with_execution_project"


@pytest.fixture(scope="session")
def bigquery_with_execution_project_manifest_path(bigquery_with_execution_project_jaffle_dir):
    dbt = DbtCliResource(project_dir=os.fspath(bigquery_with_execution_project_jaffle_dir))
    dbt.cli(["deps"]).wait()
    dbt_parse_invocation = dbt.cli(["parse"]).wait()
    manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
    yield manifest_path
