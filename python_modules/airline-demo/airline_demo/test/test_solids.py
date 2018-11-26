from dagster import execute_pipeline

from airline_demo.solids import (
    define_airline_demo_spark_ingest_pipeline,
)


def test_pipeline():
    result = execute_pipeline(
        define_airline_demo_spark_ingest_pipeline(),
        {
            'context': {
                # 'cloud': {
                #     'config': {
                #         'redshift_username': '',
                #         'redshift_password': '',
                #         'redshift_hostname': '',
                #         'redshift_db_name': '',
                #     }
                # },
                # 'test': {
                #     'config': {
                #         'redshift_username': '',
                #         'redshift_password': '',
                #         'redshift_hostname': '',
                #         'redshift_db_name': '',
                #     }
                # },
                'local': {
                    'config': {
                        'postgres_username': '',
                        'postgres_password': '',
                        'postgres_hostname': '',
                        'postgres_db_name': '',
                    }
                },
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
                'download_april_on_time_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key':
                        'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip',
                    }
                },
                'download_may_on_time_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key':
                        'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip',
                    }
                },
                'download_june_on_time_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key':
                        'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip',
                    }
                },
                'download_q2_coupon_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip',
                    }
                },
                'download_q2_market_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'Origin_and_Destination_Survey_DB1BMarket_2018_2.zip',
                    }
                },
                'download_q2_ticket_data': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'Origin_and_Destination_Survey_DB1BTicket_2018_2.zip',
                    }
                },
                'download_q2_sfo_weather': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'sfo_q2_weather.txt',
                    }
                },
                'ingest_q2_coupon_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2/Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv'
                    }
                },
                'ingest_q2_market_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BMarket_2018_2/Origin_and_Destination_Survey_DB1BMarket_2018_2.csv'
                    }
                },
                'ingest_june_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv'
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
                        'input_csv': 'q2_sfo_weather.txt'  # FIXME
                    }
                },
                'ingest_april_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv'
                    }
                },
                'subsample_may_on_time_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'ingest_q2_ticket_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BTicket_2018_2/Origin_and_Destination_Survey_DB1BTicket_2018_2.csv'
                    }
                },
                'ingest_may_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv'
                    }
                },
                'load_april_weather_and_on_time_data': {
                    'config': {
                        's3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                        'table_name': 'april_weather_and_on_time_data',
                    }
                },
                'load_may_weather_and_on_time_data': {
                    'config': {
                        's3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                        'table_name': 'may_weather_and_on_time_data',
                    }
                },
                'load_june_weather_and_on_time_data': {
                    'config': {
                        's3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                        'table_name': 'june_weather_and_on_time_data',
                    }
                },
                'load_q2_coupon_data': {
                    'config': {
                        's3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                        'table_name': 'q2_coupon_data',
                    }
                },
                'load_q2_market_data': {
                    'config': {
                        's3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                        'table_name': 'q2_market_data',
                    }
                },
                'load_q2_ticket_data': {
                    'config': {
                        's3_temp_dir': 's3n://airline-demo-redshift-spark/temp/',
                        'table_name': 'q2_ticket_data',
                    }
                }
            },
        },
    )
    assert result.success
