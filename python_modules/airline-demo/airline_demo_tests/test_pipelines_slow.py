import datetime

from dagster import execute_pipeline

from dagster.utils import script_relative_path
from dagster.utils.yaml_utils import load_yaml_from_glob_list

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import db, nettest, slow, spark


@slow
@spark
def test_pipeline_ingest():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/local_base.yml'),
            script_relative_path('../environments/local_ingest.yml'),
        ]
    )

    result = execute_pipeline(define_airline_demo_ingest_pipeline(), config_object)
    assert result.success


@db
@slow
@spark
def test_pipeline_warehouse():
    now = datetime.datetime.utcnow()
    timestamp = now.strftime('%Y_%m_%d_%H_%M_%S')
    result = execute_pipeline(
        define_airline_demo_warehouse_pipeline(),
        {
            'context': {
                'local': {
                    'resources': {
                        'db_info': {
                            'config': {
                                'postgres_username': 'test',
                                'postgres_password': 'test',
                                'postgres_hostname': 'localhost',
                                'postgres_db_name': 'test',
                            }
                        }
                    }
                }
            },
            'solids': {
                'db_url': {'config': 'postgresql://test:test@127.0.0.1:5432/test'},
                'upload_outbound_avg_delay_pdf_plots': {
                    'config': {
                        'bucket': 'dagster-airline-demo-sink',
                        'key': 'sfo_outbound_avg_delay_plots_{timestamp}.pdf'.format(
                            timestamp=timestamp
                        ),
                    }
                },
                'upload_delays_vs_fares_pdf_plots': {
                    'config': {
                        'bucket': 'dagster-airline-demo-sink',
                        'key': 'delays_vs_fares_{timestamp}.pdf'.format(timestamp=timestamp),
                    }
                },
                'upload_delays_by_geography_pdf_plots': {
                    'config': {
                        'bucket': 'dagster-airline-demo-sink',
                        'key': 'delays_by_geography_{timestamp}.pdf'.format(timestamp=timestamp),
                    }
                },
            },
        },
    )

    assert result.success
