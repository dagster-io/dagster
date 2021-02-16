import os
import uuid
from unittest import mock

import boto3
import psycopg2
import pytest
from dagster import ModeDefinition, execute_solid, solid
from dagster_aws.redshift import FakeRedshiftResource, fake_redshift_resource, redshift_resource

REDSHIFT_ENV = {
    "resources": {
        "redshift": {
            "config": {
                "host": "foo",
                "port": 5439,
                "user": "dagster",
                "password": "baz",
                "database": "dev",
                "schema": "foobar",
            }
        }
    }
}

QUERY_RESULT = [(1,)]


def mock_execute_query_conn(*_args, **_kwargs):
    cursor_mock = mock.MagicMock(rowcount=1)
    cursor_mock.fetchall.return_value = QUERY_RESULT
    conn = mock.MagicMock(is_conn="yup")
    conn.cursor.return_value.__enter__.return_value = cursor_mock
    m = mock.MagicMock()
    m.return_value.__enter__.return_value = conn
    m.return_value = conn
    return m


@solid(required_resource_keys={"redshift"})
def single_redshift_solid(context):
    assert context.resources.redshift
    return context.resources.redshift.execute_query("SELECT 1", fetch_results=True)


@solid(required_resource_keys={"redshift"})
def multi_redshift_solid(context):
    assert context.resources.redshift
    return context.resources.redshift.execute_queries(
        ["SELECT 1", "SELECT 1", "SELECT 1"], fetch_results=True
    )


@mock.patch("psycopg2.connect", new_callable=mock_execute_query_conn)
def test_single_select(redshift_connect):
    result = execute_solid(
        single_redshift_solid,
        run_config=REDSHIFT_ENV,
        mode_def=ModeDefinition(resource_defs={"redshift": redshift_resource}),
    )
    redshift_connect.assert_called_once_with(
        host="foo",
        port=5439,
        user="dagster",
        password="baz",
        database="dev",
        schema="foobar",
        connect_timeout=5,
        sslmode="require",
    )

    assert result.success
    assert result.output_value() == QUERY_RESULT


@mock.patch("psycopg2.connect", new_callable=mock_execute_query_conn)
def test_multi_select(_redshift_connect):
    result = execute_solid(
        multi_redshift_solid,
        run_config=REDSHIFT_ENV,
        mode_def=ModeDefinition(resource_defs={"redshift": redshift_resource}),
    )
    assert result.success
    assert result.output_value() == [QUERY_RESULT] * 3


def test_fake_redshift():
    fake_mode = ModeDefinition(resource_defs={"redshift": fake_redshift_resource})

    result = execute_solid(single_redshift_solid, run_config=REDSHIFT_ENV, mode_def=fake_mode)
    assert result.success
    assert result.output_value() == FakeRedshiftResource.QUERY_RESULT

    result = execute_solid(multi_redshift_solid, run_config=REDSHIFT_ENV, mode_def=fake_mode)
    assert result.success
    assert result.output_value() == [FakeRedshiftResource.QUERY_RESULT] * 3


REDSHIFT_CREATE_TABLE_QUERY = """CREATE TABLE IF NOT EXISTS VENUE1(
VENUEID SMALLINT,
VENUENAME VARCHAR(100),
VENUECITY VARCHAR(30),
VENUESTATE CHAR(2),
VENUESEATS INTEGER
) DISTSTYLE EVEN;
"""

REDSHIFT_LOAD_FILE_CONTENTS = b"""
7|BMO Field|Toronto|ON|0
16|TD Garden|Boston|MA|0
23|The Palace of Auburn Hills|Auburn Hills|MI|0
28|American Airlines Arena|Miami|FL|0
37|Staples Center|Los Angeles|CA|0
42|FedExForum|Memphis|TN|0
52|PNC Arena|Raleigh|NC  ,25   |0
59|Scotiabank Saddledome|Calgary|AB|0
66|SAP Center|San Jose|CA|0
73|Heinz Field|Pittsburgh|PA|65050
""".strip()

REDSHIFT_FAILED_LOAD_QUERY = """
SELECT le.query,
TRIM(le.err_reason) AS err_reason,
TRIM(le.filename) AS filename,
le.line_number AS line_number,
le.raw_line AS raw_line,
le.raw_field_value AS raw_value
FROM stl_load_errors le
WHERE le.query
AND le.query = pg_last_copy_id()
LIMIT 1;
"""


@pytest.mark.skipif(
    "AWS_REDSHIFT_TEST_DO_IT_LIVE" not in os.environ,
    reason="This test only works with a live Redshift cluster",
)
def test_live_redshift(s3_bucket):
    """
    This test is based on:

    https://aws.amazon.com/premiumsupport/knowledge-center/redshift-stl-load-errors/

    Requires the following environment variables:

    AWS_ACCOUNT_ID - AWS account ID to use
    REDSHIFT_LOAD_IAM_ROLE - IAM role to use for Redshift load
    REDSHIFT_ENDPOINT - Redshift URL
    REDSHIFT_PASSWORD - Redshift password

    """

    # Put file to load on S3
    file_key = uuid.uuid4().hex
    client = boto3.client("s3")
    client.put_object(Body=REDSHIFT_LOAD_FILE_CONTENTS, Bucket=s3_bucket, Key=file_key)

    @solid(required_resource_keys={"redshift"})
    def query(context):
        assert context.resources.redshift

        # First, create table:
        context.resources.redshift.execute_query(REDSHIFT_CREATE_TABLE_QUERY)

        def error_callback(error, cursor, _log):
            assert (
                str(error).strip()
                == "Load into table 'venue1' failed.  Check 'stl_load_errors' system table for details."
            )
            cursor.execute(REDSHIFT_FAILED_LOAD_QUERY)
            res = cursor.fetchall()
            assert res[0][1] == "Char length exceeds DDL length"
            assert res[0][2] == "s3://{s3_bucket}/{file_key}".format(
                s3_bucket=s3_bucket, file_key=file_key
            )
            assert res[0][3] == 7
            assert res[0][4].strip() == "52|PNC Arena|Raleigh|NC  ,25   |0"
            assert res[0][5].strip() == "NC  ,25"
            raise error

        return context.resources.redshift.execute_query(
            """COPY venue1 FROM 's3://{s3_bucket}/{file_key}'
            IAM_ROLE 'arn:aws:iam::{AWS_ACCOUNT_ID}:role/{REDSHIFT_LOAD_IAM_ROLE}'
            DELIMITER '|';
            """.format(
                s3_bucket=s3_bucket,
                file_key=file_key,
                AWS_ACCOUNT_ID=os.environ["AWS_ACCOUNT_ID"],
                REDSHIFT_LOAD_IAM_ROLE=os.environ["REDSHIFT_LOAD_IAM_ROLE"],
            ),
            fetch_results=True,
            error_callback=error_callback,
        )

    with pytest.raises(psycopg2.InternalError):
        execute_solid(
            query,
            run_config={
                "resources": {
                    "redshift": {
                        "config": {
                            "host": {"env": "REDSHIFT_ENDPOINT"},
                            "port": 5439,
                            "user": "dagster",
                            "password": {"env": "REDSHIFT_PASSWORD"},
                            "database": "dev",
                        }
                    }
                }
            },
            mode_def=ModeDefinition(resource_defs={"redshift": redshift_resource}),
        )
