import datetime
import sys
import uuid
from unittest import mock

import google
import google.api_core.exceptions
import pandas as pd
import pytest
from dagster import DagsterExecutionStepExecutionError, List, Nothing, job, op
from dagster._config import process_config, validate_config
from dagster._core.definitions import create_run_config_schema
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster_gcp import (
    bigquery_resource,
    bq_create_dataset,
    bq_delete_dataset,
    bq_op_for_queries,
    import_df_to_bq,
    import_gcs_paths_to_bq,
)
from dagster_pandas import DataFrame
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def dataset_exists(name):
    """Check if dataset exists - ensures we have properly cleaned up after tests and haven't leaked
    any datasets.
    """
    client = bigquery.Client()
    dataset_ref = client.dataset(name)

    try:
        client.get_dataset(dataset_ref)
        return True
    except NotFound:
        return False


def get_dataset():
    """Creates unique dataset names of the form: test_ds_83791a53."""
    return "test_ds_" + str(uuid.uuid4()).replace("-", "_")


@pytest.mark.integration
def test_simple_queries():
    @job(resource_defs={"bigquery": bigquery_resource})
    def bq_test():
        bq_op_for_queries(
            [
                # Toy example query
                "SELECT 1 AS field1, 2 AS field2;",
                # Test access of public BQ historical dataset (only processes ~2MB here)
                """SELECT *
            FROM `weathersource-com.pub_weather_data_samples.sample_weather_history_anomaly_us_zipcode_daily`
            ORDER BY postal_code ASC, date_valid_std ASC
            LIMIT 1""",
            ]
        ).alias("bq_query_op")()

    res = bq_test.execute_in_process()
    assert res.success

    values = res.output_for_node("bq_query_op")
    for df in values:
        assert isinstance(df, pd.DataFrame)
    assert values[0].to_dict("list") == {"field1": [1], "field2": [2]}
    assert values[1].to_dict("list") == {
        "postal_code": ["02101"],
        "country": ["US"],
        "date_valid_std": [datetime.date(2014, 1, 1)],
        "doy_std": [1],
        "avg_temperature_air_2m_f": [25.05],
        "avg_temperature_anomaly_air_2m_f": [-7.81],
        "tot_precipitation_in": [0.0],
        "tot_precipitation_anomaly_in": [-0.28],
        "tot_snowfall_in": [0.0],
        "tot_snowfall_anomaly_in": [-1.36],
        "avg_wind_speed_10m_mph": [7.91],
        "avg_wind_speed_10m_anomaly_mph": [-1.85],
    }


def test_bad_config():
    configs_and_expected_errors = [
        (
            # Create disposition must match enum values
            {"create_disposition": "this is not a valid create disposition"},
            (
                "Value at path root:ops:test:config:query_job_config:create_disposition not in enum"
                " type BQCreateDisposition"
            ),
        ),
        (
            # Priority must match enum values
            {"priority": "this is not a valid priority"},
            (
                "Value at path root:ops:test:config:query_job_config:priority not in enum type"
                " BQPriority got this is not a valid priority"
            ),
        ),
        (
            # Schema update options must be a list
            {"schema_update_options": "this is not valid schema update options"},
            (
                "Value at path root:ops:test:config:query_job_config:schema_update_options must be"
                ' list. Expected: "[BQSchemaUpdateOption]"'
            ),
        ),
        (
            {"schema_update_options": ["this is not valid schema update options"]},
            (
                "Value at path root:ops:test:config:query_job_config:schema_update_options[0] not"
                " in enum type BQSchemaUpdateOption"
            ),
        ),
        (
            {"write_disposition": "this is not a valid write disposition"},
            (
                "Value at path root:ops:test:config:query_job_config:write_disposition not in enum"
                " type BQWriteDisposition"
            ),
        ),
    ]

    @job(resource_defs={"bigquery": bigquery_resource})
    def test_config():
        bq_op_for_queries(["SELECT 1"]).alias("test")()

    env_type = create_run_config_schema(test_config).config_type
    for config_fragment, error_message in configs_and_expected_errors:
        config = {"ops": {"test": {"config": {"query_job_config": config_fragment}}}}
        result = validate_config(env_type, config)
        assert error_message in result.errors[0].message  # pyright: ignore[reportOptionalSubscript]

    configs_and_expected_validation_errors = [
        (
            {"default_dataset": "this is not a valid dataset"},
            "Datasets must be of the form",  # project_name.dataset_name',
        ),
        (
            {"destination": "this is not a valid table"},
            "Tables must be of the form",  # project_name.dataset_name.table_name'
        ),
    ]

    for config_fragment, error_message in configs_and_expected_validation_errors:
        config = {"ops": {"test": {"config": {"query_job_config": config_fragment}}}}
        result = process_config(env_type, config)
        assert error_message in result.errors[0].message  # pyright: ignore[reportOptionalSubscript]


@pytest.mark.integration
def test_create_delete_dataset():
    client = bigquery.Client()
    dataset = get_dataset()

    @job(resource_defs={"bigquery": bigquery_resource})
    def create_dataset():
        bq_create_dataset.alias("create_op")()

    result = create_dataset.execute_in_process(
        run_config={"ops": {"create_op": {"config": {"dataset": dataset, "exists_ok": True}}}}
    )
    assert result.success

    with pytest.raises(
        google.api_core.exceptions.Conflict,
        match=f"Already Exists: Dataset {client.project}:{dataset}",
    ):
        create_dataset.execute_in_process(
            run_config={"ops": {"create_op": {"config": {"dataset": dataset, "exists_ok": False}}}}
        )

    @job(resource_defs={"bigquery": bigquery_resource})
    def delete_dataset():
        bq_delete_dataset.alias("delete_op")()

    # Delete should succeed
    result = delete_dataset.execute_in_process(
        run_config={"ops": {"delete_op": {"config": {"dataset": dataset}}}}
    )
    assert result.success

    # Delete non-existent with "not_found_ok" should succeed
    result = delete_dataset.execute_in_process(
        run_config={"ops": {"delete_op": {"config": {"dataset": dataset, "not_found_ok": True}}}}
    )
    assert result.success

    # Delete non-existent with "not_found_ok" False should fail
    with pytest.raises(
        google.api_core.exceptions.NotFound,
        match=f"Not found: Dataset {client.project}:{dataset}",
    ):
        result = delete_dataset.execute_in_process(
            run_config={
                "ops": {"delete_op": {"config": {"dataset": dataset, "not_found_ok": False}}}
            }
        )

    assert not dataset_exists(dataset)


# See: https://github.com/dagster-io/dagster/issues/1711
@pytest.mark.skip
def test_pd_df_load():
    dataset = get_dataset()
    table = "{}.{}".format(dataset, "df")

    test_df = pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    create_op = bq_create_dataset.alias("create_op")
    load_op = import_df_to_bq.alias("load_op")
    query_op = bq_op_for_queries([f"SELECT num1, num2 FROM {table}"]).alias("query_op")
    delete_op = bq_delete_dataset.alias("delete_op")

    @op(
        ins={"success": In(Nothing)},
        out=Out(DataFrame),
    )
    def return_df(_context):
        return test_df

    @job(resource_defs={"bigquery": bigquery_resource})
    def bq_circle_of_life():
        delete_op(query_op(load_op(return_df(create_op()))))

    result = bq_circle_of_life.execute_in_process(
        run_config={
            "ops": {
                "create_op": {"config": {"dataset": dataset, "exists_ok": True}},
                "load_op": {"config": {"destination": table}},
                "delete_op": {"config": {"dataset": dataset, "delete_contents": True}},
            }
        }
    )
    assert result.success

    values = result.output_for_node("query_op")
    assert values[0].to_dict() == test_df.to_dict()

    # BQ loads should throw an exception if pyarrow and fastparquet aren't available
    with mock.patch.dict(sys.modules, {"pyarrow": None, "fastparquet": None}):
        with pytest.raises(DagsterExecutionStepExecutionError) as exc_info:
            bq_circle_of_life.execute_in_process(
                run_config={
                    "ops": {
                        "create_op": {"config": {"dataset": dataset, "exists_ok": True}},
                        "load_op": {"config": {"destination": table}},
                        "delete_op": {"config": {"dataset": dataset, "delete_contents": True}},
                    }
                }
            )
        assert (
            "loading data to BigQuery from pandas DataFrames requires either pyarrow or fastparquet"
            " to be installed" in str(exc_info.value.user_exception)
        )

        @job(resource_defs={"bigquery": bigquery_resource})
        def cleanup_bq():
            delete_op()

        result = cleanup_bq.execute_in_process(
            run_config={
                "ops": {"delete_op": {"config": {"dataset": dataset, "delete_contents": True}}}
            }
        )
        assert result.success

    assert not dataset_exists(dataset)


# See: https://github.com/dagster-io/dagster/issues/1711
@pytest.mark.skip
def test_gcs_load():
    dataset = get_dataset()
    table = "{}.{}".format(dataset, "df")

    create_op = bq_create_dataset.alias("create_op")
    query_op = bq_op_for_queries(
        [f"SELECT string_field_0, string_field_1 FROM {table} ORDER BY string_field_0 ASC LIMIT 1"]
    ).alias("query_op")
    delete_op = bq_delete_dataset.alias("delete_op")

    @op(
        ins={"success": In(Nothing)},
        out=Out(List[str]),
    )
    def return_gcs_uri(_context):
        return ["gs://cloud-samples-data/bigquery/us-states/us-states.csv"]

    @job(resource_defs={"bigquery": bigquery_resource})
    def bq_from_gcs():
        delete_op(query_op(import_gcs_paths_to_bq(return_gcs_uri(create_op()))))

    result = bq_from_gcs.execute_in_process(
        run_config={
            "ops": {
                "create_op": {"config": {"dataset": dataset, "exists_ok": True}},
                "import_gcs_paths_to_bq": {
                    "config": {
                        "destination": table,
                        "load_job_config": {
                            "autodetect": True,
                            "skip_leading_rows": 1,
                            "source_format": "CSV",
                            "write_disposition": "WRITE_TRUNCATE",
                        },
                    }
                },
                "delete_op": {"config": {"dataset": dataset, "delete_contents": True}},
            }
        }
    )
    assert result.success

    values = result.output_for_node("query_op")
    assert values[0].to_dict() == {
        "string_field_0": {0: "Alabama"},
        "string_field_1": {0: "AL"},
    }

    assert not dataset_exists(dataset)
