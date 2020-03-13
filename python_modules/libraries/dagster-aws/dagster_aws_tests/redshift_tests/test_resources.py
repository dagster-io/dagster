from dagster_aws import fake_redshift_resource, redshift_resource
from dagster_aws.redshift.resources import FakeRedshiftResource

from dagster import ModeDefinition, execute_solid, solid
from dagster.seven import mock

REDSHIFT_ENV = {
    'resources': {
        'redshift': {
            'config': {
                'host': 'foo',
                'port': 5439,
                'user': 'dagster',
                'password': 'baz',
                'database': 'dev',
                'schema': 'foobar',
            }
        }
    }
}

QUERY_RESULT = [(1,)]


def mock_execute_query_conn(*_args, **_kwargs):
    cursor_mock = mock.MagicMock(rowcount=1)
    cursor_mock.fetchall.return_value = QUERY_RESULT
    conn = mock.MagicMock(is_conn='yup')
    conn.cursor.return_value.__enter__.return_value = cursor_mock
    m = mock.MagicMock()
    m.return_value.__enter__.return_value = conn
    m.return_value = conn
    return m


@solid(required_resource_keys={'redshift'})
def single_redshift_solid(context):
    assert context.resources.redshift
    return context.resources.redshift.execute_query('SELECT 1', fetch_results=True)


@solid(required_resource_keys={'redshift'})
def multi_redshift_solid(context):
    assert context.resources.redshift
    return context.resources.redshift.execute_queries(
        ['SELECT 1', 'SELECT 1', 'SELECT 1'], fetch_results=True
    )


@mock.patch('psycopg2.connect', new_callable=mock_execute_query_conn)
def test_single_select(redshift_connect):
    result = execute_solid(
        single_redshift_solid,
        environment_dict=REDSHIFT_ENV,
        mode_def=ModeDefinition(resource_defs={'redshift': redshift_resource}),
    )
    redshift_connect.assert_called_once_with(
        host='foo',
        port=5439,
        user='dagster',
        password='baz',
        database='dev',
        schema='foobar',
        connect_timeout=5,
        sslmode='require',
    )

    assert result.success
    assert result.output_value() == QUERY_RESULT


@mock.patch('psycopg2.connect', new_callable=mock_execute_query_conn)
def test_multi_select(_redshift_connect):
    result = execute_solid(
        multi_redshift_solid,
        environment_dict=REDSHIFT_ENV,
        mode_def=ModeDefinition(resource_defs={'redshift': redshift_resource}),
    )
    assert result.success
    assert result.output_value() == [QUERY_RESULT] * 3


def test_fake_redshift():
    fake_mode = ModeDefinition(resource_defs={'redshift': fake_redshift_resource})

    result = execute_solid(single_redshift_solid, environment_dict=REDSHIFT_ENV, mode_def=fake_mode)
    assert result.success
    assert result.output_value() == FakeRedshiftResource.QUERY_RESULT

    result = execute_solid(multi_redshift_solid, environment_dict=REDSHIFT_ENV, mode_def=fake_mode)
    assert result.success
    assert result.output_value() == [FakeRedshiftResource.QUERY_RESULT] * 3
