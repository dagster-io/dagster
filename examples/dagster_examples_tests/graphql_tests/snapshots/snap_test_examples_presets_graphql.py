# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_presets_on_examples 1'] = {
    'pipeline': {
        'name': 'airline_demo_ingest_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''resources:
  db_info:
    config:
      postgres_db_name: test
      postgres_hostname: localhost
      postgres_password: test
      postgres_username: test
  file_cache:
    config:
      target_folder: /tmp/dagster/airline_data/file_cache
solids:
  april_on_time_s3_to_df:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip
  download_q2_sfo_weather:
    inputs:
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/sfo_q2_weather.txt
  join_q2_data:
    config:
      subsample_pct: 100
  june_on_time_s3_to_df:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip
  load_q2_on_time_data:
    config:
      table_name: q2_on_time_data
  load_q2_sfo_weather:
    config:
      table_name: q2_sfo_weather
  master_cord_s3_to_df:
    inputs:
      archive_member:
        value: 954834304_T_MASTER_CORD.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/954834304_T_MASTER_CORD.zip
  may_on_time_s3_to_df:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip
  process_q2_coupon_data:
    config:
      subsample_pct: 100
      table_name: q2_coupon_data
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip
  process_q2_market_data:
    config:
      subsample_pct: 100
      table_name: q2_market_data
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BMarket_2018_2.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/Origin_and_Destination_Survey_DB1BMarket_2018_2.zip
  process_q2_ticket_data:
    config:
      subsample_pct: 100
      table_name: q2_ticket_data
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BTicket_2018_2.csv
      s3_coordinate:
        bucket: dagster-airline-demo-source-data
        key: test/Origin_and_Destination_Survey_DB1BTicket_2018_2.zip
''',
                'mode': 'local',
                'name': 'local_fast',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''resources:
  db_info:
    config:
      postgres_db_name: test
      postgres_hostname: localhost
      postgres_password: test
      postgres_username: test
  file_cache:
    config:
      target_folder: /tmp/dagster/airline_data/file_cache
solids:
  process_on_time_data:
    solids:
      april_on_time_s3_to_df:
        inputs:
          archive_member:
            value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip
      join_q2_data:
        config:
          subsample_pct: 100
      june_on_time_s3_to_df:
        inputs:
          archive_member:
            value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip
      load_q2_on_time_data:
        config:
          table_name: q2_on_time_data
      master_cord_s3_to_df:
        inputs:
          archive_member:
            value: 954834304_T_MASTER_CORD.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/954834304_T_MASTER_CORD.zip
      may_on_time_s3_to_df:
        inputs:
          archive_member:
            value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip
  process_q2_coupon_data:
    solids:
      load_data_to_database_from_spark:
        config:
          table_name: q2_coupon_data
      s3_to_df:
        inputs:
          archive_member:
            value: Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip
      subsample_spark_dataset:
        config:
          subsample_pct: 100
  process_q2_market_data:
    solids:
      load_data_to_database_from_spark:
        config:
          table_name: q2_market_data
      s3_to_df:
        inputs:
          archive_member:
            value: Origin_and_Destination_Survey_DB1BMarket_2018_2.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/Origin_and_Destination_Survey_DB1BMarket_2018_2.zip
      subsample_spark_dataset:
        config:
          subsample_pct: 100
  process_q2_ticket_data:
    solids:
      load_data_to_database_from_spark:
        config:
          table_name: q2_ticket_data
      s3_to_df:
        inputs:
          archive_member:
            value: Origin_and_Destination_Survey_DB1BTicket_2018_2.csv
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/Origin_and_Destination_Survey_DB1BTicket_2018_2.zip
      subsample_spark_dataset:
        config:
          subsample_pct: 100
  sfo_weather_data:
    solids:
      download_q2_sfo_weather:
        inputs:
          s3_coordinate:
            bucket: dagster-airline-demo-source-data
            key: test/source_data/sfo_q2_weather.txt
      load_q2_sfo_weather:
        config:
          table_name: q2_sfo_weather
''',
                'mode': 'local',
                'name': 'local_full',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 2'] = {
    'pipeline': {
        'name': 'airline_demo_warehouse_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''resources:
  db_info:
    config:
      postgres_db_name: test
      postgres_hostname: localhost
      postgres_password: test
      postgres_username: test
  file_cache:
    config:
      target_folder: /tmp/dagster/airline_data/file_cache
solids:
  process_delays_by_geo:
    solids:
      upload_delays_by_geography_pdf_plots:
        config:
          Bucket: dagster-scratch-80542c2
          Key: airline_outputs/delays_by_geography.pdf
  upload_delays_vs_fares_pdf_plots:
    config:
      Bucket: dagster-scratch-80542c2
      Key: airline_outputs/delays_vs_fares.pdf
  upload_outbound_avg_delay_pdf_plots:
    config:
      Bucket: dagster-scratch-80542c2
      Key: airline_outputs/sfo_outbound_avg_delay_plots.pdf
''',
                'mode': 'local',
                'name': 'local',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 3'] = {
    'pipeline': {
        'name': 'composition',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 4'] = {
    'pipeline': {
        'name': 'error_monster',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''resources:
  errorable_resource:
    config:
      throw_on_resource_init: false
solids:
  end:
    config:
      return_wrong_type: false
      throw_in_solid: false
  middle:
    config:
      return_wrong_type: false
      throw_in_solid: false
  start:
    config:
      return_wrong_type: false
      throw_in_solid: false
''',
                'mode': 'errorable_mode',
                'name': 'passing',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 5'] = {
    'pipeline': {
        'name': 'event_ingest_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''resources:
  snowflake:
    config:
      account: << SET ME >>
      database: TESTDB
      password: << SET ME >>
      schema: TESTSCHEMA
      user: << SET ME >>
      warehouse: TINY_WAREHOUSE
solids:
  download_from_s3_to_file:
    config:
      bucket: elementl-public
      key: example-json.gz
      skip_if_present: true
      target_folder: /tmp/dagster/events/data
  event_ingest:
    config:
      application_arguments: --local-path /tmp/dagster/events/data --date 2019-01-01
      application_jar: /tmp/dagster/events/events-assembly-0.1.0-SNAPSHOT.jar
      deploy_mode: client
      master_url: local[*]
      spark_conf:
        spark:
          app:
            name: test_app
      spark_outputs:
      - /tmp/dagster/events/data
''',
                'mode': 'default',
                'name': 'default',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 6'] = {
    'pipeline': {
        'name': 'jaffle_pipeline',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 7'] = {
    'pipeline': {
        'name': 'log_spew',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 8'] = {
    'pipeline': {
        'name': 'many_events',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 9'] = {
    'pipeline': {
        'name': 'pandas_hello_world_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num_df:
        csv:
          path: data/num_prod.csv
''',
                'mode': 'default',
                'name': 'prod',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num_df:
        csv:
          path: data/num.csv
''',
                'mode': 'default',
                'name': 'test',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 10'] = {
    'pipeline': {
        'name': 'pandas_hello_world_pipeline_with_read_csv',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 11'] = {
    'pipeline': {
        'name': 'pyspark_pagerank',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 12'] = {
    'pipeline': {
        'name': 'sleepy_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''execution:
  multiprocess: {}
solids:
  giver:
    config:
    - 2
    - 2
    - 2
    - 2
storage:
  filesystem: {}
''',
                'mode': 'default',
                'name': 'multi',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 13'] = {
    'pipeline': {
        'name': 'stdout_spew_pipeline',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 14'] = {
    'pipeline': {
        'name': 'unreliable_pipeline',
        'presets': [
        ]
    }
}
