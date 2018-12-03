"""Unit and pipeline tests for the airline_demo.

As is common in real-world pipelines, we want to test some fairly heavy-weight operations,
requiring, e.g., a connection to S3, Spark, and a database. 

We lever pytest marks to isolate subsets of tests with different requirements. E.g., to run only
those tests that don't require Spark, `pytest -m "not spark"`.
"""
import logging
import os

import pyspark
import pytest

from collections import namedtuple

from dagster import (
    config,
    DependencyDefinition,
    execute_pipeline,
    ExecutionContext,
    lambda_solid,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidInstance,
)
from dagster.utils.test import (define_stub_solid, execute_solid)

from airline_demo.pipelines import (
    _create_s3_session,
    _create_spark_session_local,
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)
from airline_demo.solids import (
    create_sql_solid,
    download_from_s3,
    ingest_csv_to_spark,
    thunk,
    unzip_file,
)

S3Resources = namedtuple('S3Resources', ('s3', ))

SparkResources = namedtuple('SparkResources', ('spark', ))


def _s3_context():
    return {
        'test': PipelineContextDefinition(
            context_fn=(
                lambda info: ExecutionContext.console_logging(
                    log_level=logging.DEBUG,
                    resources=S3Resources(
                        _create_s3_session(signed=False),
                    )
                )
            ),
        )
    }


def _spark_context():
    return {
        'test': PipelineContextDefinition(
            context_fn=(
                lambda info: ExecutionContext.console_logging(
                    log_level=logging.DEBUG,
                    resources=SparkResources(
                        _create_spark_session_local(),
                    )
                )
            ),
        )
    }


def test_create_sql_solid_with_bad_materialization_strategy():
    with pytest.raises() as e:
        create_sql_solid('foo', 'select * from bar', 'view')
        raise NotImplementedError()


def test_create_sql_solid_without_table_name():
    with pytest.raises() as e:
        create_sql_solid('foo', 'select * from bar', 'table')
        raise NotImplementedError()


def test_create_sql_solid():
    result = create_sql_solid('foo', 'select * from bar', 'table', 'quux')
    raise NotImplementedError()


def test_thunk():
    result = execute_solid(
        PipelineDefinition([thunk]), 'thunk', environment={'solids': {
            'thunk': {
                'config': 'foo'
            }
        }}
    )
    assert result.success
    assert result.transformed_value() == 'foo'


@pytest.mark.nettest
def test_download_from_s3():
    result = execute_solid(
        PipelineDefinition([download_from_s3], context_definitions=_s3_context()),
        'download_from_s3',
        environment={
            'context': {
                'test': {}
            },
            'solids': {
                'download_from_s3': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'test/test_file'
                    }
                }
            }
        }
    )
    assert result.success
    assert result.transformed_value() == 'test/test_file'
    assert os.path.isfile(result.transformed_value())
    with open(result.transformed_value(), 'r') as fd:
        assert fd.read() == 'test\n'


def test_unzip_file():
    @lambda_solid
    def nonce():
        return None

    result = execute_solid(
        PipelineDefinition(
            solids=[nonce, unzip_file],
            dependencies={
                'unzip_file': {
                    'archive_path': DependencyDefinition('nonce'),
                    'archive_member': DependencyDefinition('nonce')
                }
            }
        ),
        'unzip_file',
        inputs={
            'archive_path': os.path.join(os.path.dirname(__file__), 'data/test.zip'),
            'archive_member': 'test/test_file'
        },
        environment={'solids': {
            'unzip_file': {
                'config': {
                    'skip_if_present': False
                }
            }
        }}
    )
    assert result.success
    assert result.transformed_value() == os.path.join(
        os.path.dirname(__file__), 'data', 'test/test_file'
    )
    assert os.path.isfile(result.transformed_value())
    with open(result.transformed_value(), 'r') as fd:
        assert fd.read() == 'test\n'


@pytest.mark.spark
def test_ingest_csv_to_spark():
    @lambda_solid
    def nonce():
        return None

    result = execute_solid(
        PipelineDefinition(
            [nonce, ingest_csv_to_spark],
            dependencies={'ingest_csv_to_spark': {
                'input_csv': DependencyDefinition('nonce'),
            }},
            context_definitions=_spark_context(),
        ),
        'ingest_csv_to_spark',
        inputs={
            'input_csv': os.path.join(os.path.dirname(__file__), 'data/test.csv'),
        },
        environment={
            'context': {
                'test': {}
            },
            'solids': {
                'ingest_csv_to_spark': {
                    'config': {}
                }
            }
        }
    )
    assert result.success
    assert isinstance(result.transformed_value(), pyspark.sql.dataframe.DataFrame)
    assert result.transformed_value().head()[0] == '1'


@pytest.mark.spark
@pytest.mark.postgres
def test_load_data_to_postgres_from_spark_postgres():
    raise NotImplementedError()


@pytest.mark.nettest
@pytest.mark.spark
@pytest.mark.redshift
def test_load_data_to_redshift_from_spark():
    raise NotImplementedError()


@pytest.mark.spark
def test_subsample_spark_dataset():
    raise NotImplementedError()


@pytest.mark.spark
def test_join_spark_data_frame():
    raise NotImplementedError()


@pytest.mark.nettest
@pytest.mark.slow
def test_pipeline_download():
    result = execute_pipeline(
        define_airline_demo_download_pipeline(), {
            'context': {
                'local': {
                    'config': {
                        'postgres_username': 'test',
                        'postgres_password': 'test',
                        'postgres_hostname': '127.0.0.1',
                        'postgres_db_name': 'test',
                        'db_dialect': 'postgres',
                    }
                }
            },
            'solids': {
                'april_on_time_data_filename': {
                    'config':
                    'On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv'
                },
                'may_on_time_data_filename': {
                    'config':
                    'On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv'
                },
                'june_on_time_data_filename': {
                    'config':
                    'On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv'
                },
                'q2_coupon_data_filename': {
                    'config': 'Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv'
                },
                'q2_market_data_filename': {
                    'config': 'Origin_and_Destination_Survey_DB1BMarket_2018_2.csv'
                },
                'q2_ticket_data_filename': {
                    'config': 'Origin_and_Destination_Survey_DB1BTicket_2018_2.csv'
                },
                'master_cord_data_filename': {
                    'config': '954834304_T_MASTER_CORD.csv'
                },
                'download_april_on_time_data': {
                    'config': {
                        'bucket':
                        'dagster-airline-demo-source-data',
                        'key':
                        'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip',
                        'skip_if_present':
                        True,
                        'target_path':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip',
                    }
                },
                'download_may_on_time_data': {
                    'config': {
                        'bucket':
                        'dagster-airline-demo-source-data',
                        'key':
                        'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip',
                        'skip_if_present':
                        True,
                        'target_path':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip',
                    },
                },
                'download_june_on_time_data': {
                    'config': {
                        'bucket':
                        'dagster-airline-demo-source-data',
                        'key':
                        'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip',
                        'skip_if_present':
                        True,
                        'target_path':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip',
                    }
                },
                'download_q2_coupon_data': {
                    'config': {
                        'bucket':
                        'dagster-airline-demo-source-data',
                        'key':
                        'Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip',
                        'skip_if_present':
                        True,
                        'target_path':
                        'source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip',
                    }
                },
                'download_q2_market_data': {
                    'config': {
                        'bucket':
                        'dagster-airline-demo-source-data',
                        'key':
                        'Origin_and_Destination_Survey_DB1BMarket_2018_2.zip',
                        'skip_if_present':
                        True,
                        'target_path':
                        'source_data/Origin_and_Destination_Survey_DB1BMarket_2018_2.zip',
                    }
                },
                'download_q2_ticket_data': {
                    'config': {
                        'bucket':
                        'dagster-airline-demo-source-data',
                        'key':
                        'Origin_and_Destination_Survey_DB1BTicket_2018_2.zip',
                        'skip_if_present':
                        True,
                        'target_path':
                        'source_data/Origin_and_Destination_Survey_DB1BTicket_2018_2.zip',
                    }
                },
                'download_q2_sfo_weather': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'sfo_q2_weather.txt',
                        'skip_if_present': True,
                        'target_path': 'source_data/sfo_q2_weather.txt',
                    }
                },
                'download_master_cord_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': '954834304_T_MASTER_CORD.zip',
                        'skip_if_present': True,
                        'target_path': 'source_data/954834304_T_MASTER_CORD.zip',
                    }
                },
                'unzip_april_on_time_data': {
                    'config': {
                        'skip_if_present': True,
                    },
                },
                'unzip_may_on_time_data': {
                    'config': {
                        'skip_if_present': True,
                    },
                },
                'unzip_june_on_time_data': {
                    'config': {
                        'skip_if_present': True,
                    },
                },
                'unzip_q2_coupon_data': {
                    'config': {
                        'skip_if_present': True,
                    },
                },
                'unzip_q2_market_data': {
                    'config': {
                        'skip_if_present': True,
                    },
                },
                'unzip_q2_ticket_data': {
                    'config': {
                        'skip_if_present': True,
                    },
                },
                'unzip_master_cord_data': {
                    'config': {
                        'skip_if_present': True,
                    }
                }
            }
        }
    )
    assert result.success


@pytest.mark.spark
@pytest.mark.slow
def test_pipeline_ingest():
    result = execute_pipeline(
        define_airline_demo_ingest_pipeline(),
        {
            'context': {
                # 'cloud': {
                #     'config': {
                #         'redshift_username': 'airline_demo_username',
                #         'redshift_password': 'A1rline_demo_password',
                #         'redshift_hostname': 'db.airline-demo.dagster.io',
                #         'redshift_db_name': 'airline_demo',
                #         'redshift_s3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                #         'db_dialect': 'redshift',
                #     }
                # },
                # 'test': {
                #     'config': {
                #         'redshift_username': 'airline_demo_username',
                #         'redshift_password': 'A1rline_demo_password',
                #         'redshift_hostname': 'db.airline-demo.dagster.io',
                #         'redshift_db_name': 'airline_demo',
                #         'redshift_s3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                #         'db_dialect': 'redshift',
                #     }
                # },
                'local': {
                    'config': {
                        'postgres_username': 'test',
                        'postgres_password': 'test',
                        'postgres_hostname': '127.0.0.1',
                        'postgres_db_name': 'test',
                        'db_dialect': 'postgres',
                    }
                },
            },
            'solids': {
                'april_on_time_data_filename': {
                    'config':
                    'source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv'
                },
                'may_on_time_data_filename': {
                    'config':
                    'source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv'
                },
                'june_on_time_data_filename': {
                    'config':
                    'source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv'
                },
                'q2_sfo_weather_filename': {
                    'config': 'source_data/sfo_q2_weather.txt'
                },
                'q2_coupon_data_filename': {
                    'config': 'source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv'
                },
                'q2_market_data_filename': {
                    'config': 'source_data/Origin_and_Destination_Survey_DB1BMarket_2018_2.csv'
                },
                'q2_ticket_data_filename': {
                    'config': 'source_data/Origin_and_Destination_Survey_DB1BTicket_2018_2.csv'
                },
                'master_cord_data_filename': {
                    'config': 'source_data/954834304_T_MASTER_CORD.csv'
                },
                # FIXME should these be stubbed inputs instead?
                'ingest_q2_coupon_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv'
                    }
                },
                'ingest_q2_market_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BMarket_2018_2.csv'
                    }
                },
                'ingest_june_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv'
                    }
                },
                'subsample_april_on_time_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_june_on_time_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'ingest_q2_sfo_weather': {
                    'config': {
                        'input_csv': 'source_data/sfo_q2_weather.txt'  # FIXME
                    }
                },
                'ingest_april_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv'
                    }
                },
                'subsample_may_on_time_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_q2_ticket_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_q2_market_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_q2_coupon_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'ingest_q2_ticket_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BTicket_2018_2.csv'
                    }
                },
                'ingest_may_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv'
                    }
                },
                'ingest_master_cord_data': {
                    'config': {
                        'input_csv': 'source_data/954834304_T_MASTER_CORD.csv'
                    }
                },
                'join_april_on_time_data_to_master_cord_data': {
                    'config': {
                        'on_left': 'OriginAirportSeqID',
                        'on_right': 'AIRPORT_SEQ_ID',
                        'how': 'inner',
                    }
                },
                'join_may_on_time_data_to_master_cord_data': {
                    'config': {
                        'on_left': 'OriginAirportSeqID',
                        'on_right': 'AIRPORT_SEQ_ID',
                        'how': 'inner',
                    }
                },
                'join_june_on_time_data_to_master_cord_data': {
                    'config': {
                        'on_left': 'OriginAirportSeqID',
                        'on_right': 'AIRPORT_SEQ_ID',
                        'how': 'inner',
                    }
                },
                'load_april_on_time_data': {
                    'config': {
                        'table_name': 'april_on_time_data',
                    }
                },
                'load_may_on_time_data': {
                    'config': {
                        'table_name': 'may_on_time_data',
                    }
                },
                'load_june_on_time_data': {
                    'config': {
                        'table_name': 'june_on_time_data',
                    }
                },
                'load_q2_coupon_data': {
                    'config': {
                        'table_name': 'q2_coupon_data',
                    }
                },
                'load_q2_market_data': {
                    'config': {
                        'table_name': 'q2_market_data',
                    }
                },
                'load_q2_ticket_data': {
                    'config': {
                        'table_name': 'q2_ticket_data',
                    }
                },
                'load_q2_sfo_weather': {
                    'config': {
                        'table_name': 'q2_sfo_weather',
                    }
                }
            },
        },
    )
    assert result.success
