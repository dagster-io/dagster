import pytest

from dagster import execute_pipeline

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)


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
                'subsample_q2_on_time_data': {
                    'config': {
                        'subsample_pct': 100,
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
                'join_q2_on_time_data_to_master_cord_data': {
                    'config': {
                        'on_left': 'OriginAirportSeqID',
                        'on_right': 'AIRPORT_SEQ_ID',
                        'how': 'inner',
                    }
                },
                'load_q2_on_time_data': {
                    'config': {
                        'table_name': 'q2_on_time_data',
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


@pytest.mark.slow
@pytest.mark.db
@pytest.mark.spark
def test_pipeline_warehouse():
    result = execute_pipeline(
        define_airline_demo_warehouse_pipeline(),
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
                'db_url': {
                    'config': 'postgresql://test:test@127.0.0.1:5432/test'
                },
            }
        }
    )
