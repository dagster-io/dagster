# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_presets_on_examples 1'] = {
    'pipeline': {
        'name': 'sleepy',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 2'] = {
    'pipeline': {
        'name': 'error_monster',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''expectations:
  evaluate: false
resources:
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

snapshots['test_presets_on_examples 3'] = {
    'pipeline': {
        'name': 'log_spew',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 4'] = {
    'pipeline': {
        'name': 'many_events',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 5'] = {
    'pipeline': {
        'name': 'composition',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 6'] = {
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
solids:
  download_april_on_time_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip
  download_june_on_time_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip
  download_master_cord_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/954834304_T_MASTER_CORD.zip
  download_may_on_time_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip
  download_q2_coupon_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip
  download_q2_market_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/Origin_and_Destination_Survey_DB1BMarket_2018_2.zip
  download_q2_sfo_weather:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/sfo_q2_weather.txt
  download_q2_ticket_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/Origin_and_Destination_Survey_DB1BTicket_2018_2.zip
  join_q2_on_time_data_to_dest_cord_data:
    config:
      how: left_outer
      on_left: DestAirportSeqID
      on_right: DEST_AIRPORT_SEQ_ID
  join_q2_on_time_data_to_origin_cord_data:
    config:
      how: left_outer
      on_left: OriginAirportSeqID
      on_right: ORIGIN_AIRPORT_SEQ_ID
  load_q2_coupon_data:
    config:
      table_name: q2_coupon_data
  load_q2_market_data:
    config:
      table_name: q2_market_data
  load_q2_on_time_data:
    config:
      table_name: q2_on_time_data
  load_q2_sfo_weather:
    config:
      table_name: q2_sfo_weather
  load_q2_ticket_data:
    config:
      table_name: q2_ticket_data
  prefix_dest_cord_data:
    config: DEST_
  prefix_origin_cord_data:
    config: ORIGIN_
  subsample_q2_coupon_data:
    config:
      subsample_pct: 100
  subsample_q2_market_data:
    config:
      subsample_pct: 100
  subsample_q2_on_time_data:
    config:
      subsample_pct: 100
  subsample_q2_ticket_data:
    config:
      subsample_pct: 100
  unzip_april_on_time_data:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv
  unzip_june_on_time_data:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv
  unzip_master_cord_data:
    inputs:
      archive_member:
        value: 954834304_T_MASTER_CORD.csv
  unzip_may_on_time_data:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv
  unzip_q2_coupon_data:
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv
  unzip_q2_market_data:
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BMarket_2018_2.csv
  unzip_q2_ticket_data:
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BTicket_2018_2.csv
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
solids:
  download_april_on_time_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip
  download_june_on_time_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_6.zip
  download_master_cord_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/954834304_T_MASTER_CORD.zip
  download_may_on_time_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_5.zip
  download_q2_coupon_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/Origin_and_Destination_Survey_DB1BCoupon_2018_2.zip
  download_q2_market_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/Origin_and_Destination_Survey_DB1BMarket_2018_2.zip
  download_q2_sfo_weather:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/sfo_q2_weather.txt
  download_q2_ticket_data:
    config:
      bucket: dagster-airline-demo-source-data
      key: test/source_data/Origin_and_Destination_Survey_DB1BTicket_2018_2.zip
  join_q2_on_time_data_to_dest_cord_data:
    config:
      how: left_outer
      on_left: DestAirportSeqID
      on_right: DEST_AIRPORT_SEQ_ID
  join_q2_on_time_data_to_origin_cord_data:
    config:
      how: left_outer
      on_left: OriginAirportSeqID
      on_right: ORIGIN_AIRPORT_SEQ_ID
  load_q2_coupon_data:
    config:
      table_name: q2_coupon_data
  load_q2_market_data:
    config:
      table_name: q2_market_data
  load_q2_on_time_data:
    config:
      table_name: q2_on_time_data
  load_q2_sfo_weather:
    config:
      table_name: q2_sfo_weather
  load_q2_ticket_data:
    config:
      table_name: q2_ticket_data
  prefix_dest_cord_data:
    config: DEST_
  prefix_origin_cord_data:
    config: ORIGIN_
  subsample_q2_coupon_data:
    config:
      subsample_pct: 100
  subsample_q2_market_data:
    config:
      subsample_pct: 100
  subsample_q2_on_time_data:
    config:
      subsample_pct: 100
  subsample_q2_ticket_data:
    config:
      subsample_pct: 100
  unzip_april_on_time_data:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv
  unzip_june_on_time_data:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_6.csv
  unzip_master_cord_data:
    inputs:
      archive_member:
        value: 954834304_T_MASTER_CORD.csv
  unzip_may_on_time_data:
    inputs:
      archive_member:
        value: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_5.csv
  unzip_q2_coupon_data:
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BCoupon_2018_2.csv
  unzip_q2_market_data:
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BMarket_2018_2.csv
  unzip_q2_ticket_data:
    inputs:
      archive_member:
        value: Origin_and_Destination_Survey_DB1BTicket_2018_2.csv
''',
                'mode': 'local',
                'name': 'local_full',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 7'] = {
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
solids:
  upload_delays_by_geography_pdf_plots:
    config:
      Bucket: dagster-scratch
      Key: airline_outputs/delays_by_geography.pdf
  upload_delays_vs_fares_pdf_plots:
    config:
        Bucket: dagster-scratch
        Key: airline_outputs/delays_vs_fares.pdf
  upload_outbound_avg_delay_pdf_plots:
    config:
      Bucket: dagster-scratch
      Key: airline_outputs/sfo_outbound_avg_delay_plots.pdf
''',
                'mode': 'local',
                'name': 'local',
                'solidSubset': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 8'] = {
    'pipeline': {
        'name': 'event_ingest_pipeline',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 9'] = {
    'pipeline': {
        'name': 'pyspark_pagerank',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 10'] = {
    'pipeline': {
        'name': 'pandas_hello_world',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num:
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
      num:
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

snapshots['test_presets_on_examples 11'] = {
    'pipeline': {
        'name': 'papermill_pandas_hello_world_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  papermill_pandas_hello_world:
    inputs:
      df:
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
  papermill_pandas_hello_world:
    inputs:
      df:
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
