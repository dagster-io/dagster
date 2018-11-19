from dagster import execute_pipeline

from airline_demo.solids import (
    define_airline_demo_spark_ingest_pipeline
)

def test_pipeline():
    result = execute_pipeline(
        define_airline_demo_spark_ingest_pipeline(),
        {
            'context': {'cloud': {}},
            'solids': {
                'ingest_q2_coupon_data': {
                    'config': {
                        'input_csv':
                        'source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2/Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv'
                    }
                },
                'subsample_may_sfo_weather': {
                    'config': {
                        'subsample_pct': 10,
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
                'subsample_april_sfo_weather': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_april_on_time_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_june_sfo_weather': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'subsample_june_on_time_data': {
                    'config': {
                        'subsample_pct': 10,
                    }
                },
                'ingest_april_sfo_weather': {
                    'config': {
                        'input_csv': 'source_data/SFO.txt' # FIXME
                    }
                },
                'ingest_may_sfo_weather': {
                    'config': {
                        'input_csv': 'source_data/SFO.txt' # FIXME
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
                'ingest_june_sfo_weather': {
                    'config': {
                        'input_csv': 'source_data/SFO.txt' # FIXME
                    }
                },
                'ingest_may_on_time_data': {
                    'config': {
                        'input_csv':
                        'source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv'
                    }
                },
            },
        },
    )
    assert result.success
