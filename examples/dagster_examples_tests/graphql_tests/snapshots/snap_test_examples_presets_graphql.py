# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_presets_on_examples 1'] = {
    'pipelineOrError': {
        'name': 'airline_demo_ingest_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'local',
                'name': 'local_fast',
                'runConfigYaml': '''resources:
  db_info:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  file_cache:
    config:
      target_folder: /tmp/dagster/airline_data/file_cache
  pyspark:
    config:
      spark_conf:
        spark:
          jars:
            packages: com.databricks:spark-avro_2.11:3.0.0,com.databricks:spark-redshift_2.11:2.0.1,com.databricks:spark-csv_2.11:1.5.0,org.postgresql:postgresql:42.2.5,org.apache.hadoop:hadoop-aws:2.6.5,com.amazonaws:aws-java-sdk:1.7.4
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
                'solidSelection': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'local',
                'name': 'local_full',
                'runConfigYaml': '''resources:
  db_info:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  file_cache:
    config:
      target_folder: /tmp/dagster/airline_data/file_cache
  pyspark:
    config:
      spark_conf:
        spark:
          jars:
            packages: com.databricks:spark-avro_2.11:3.0.0,com.databricks:spark-redshift_2.11:2.0.1,com.databricks:spark-csv_2.11:1.5.0,org.postgresql:postgresql:42.2.5,org.apache.hadoop:hadoop-aws:2.6.5,com.amazonaws:aws-java-sdk:1.7.4
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
                'solidSelection': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'prod',
                'name': 'prod_fast',
                'runConfigYaml': '''resources:
  db_info:
    config:
      db_name:
        env: REDSHIFT_DB
      hostname:
        env: REDSHIFT_ENDPOINT
      password:
        env: REDSHIFT_PASSWORD
      port:
        env: REDSHIFT_PORT
      s3_temp_dir: dagster-scratch-80542c2
      username:
        env: REDSHIFT_USERNAME
  file_cache:
    config:
      bucket: dagster-scratch-80542c2
      key: airline-demo
  pyspark_step_launcher:
    config:
      cluster_id:
        env: EMR_CLUSTER_ID
      deploy_local_pipeline_package: true
      local_pipeline_package_path: .
      region_name: us-west-1
      spark_config:
        spark:
          jars:
            packages: com.databricks:spark-avro_2.11:3.0.0,com.databricks:spark-redshift_2.11:2.0.1,com.databricks:spark-csv_2.11:1.5.0,org.postgresql:postgresql:42.2.5,org.apache.hadoop:hadoop-aws:2.6.5,com.amazonaws:aws-java-sdk:1.7.4
      staging_bucket: dagster-scratch-80542c2
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
storage:
  s3:
    config:
      s3_bucket: dagster-scratch-80542c2
      s3_prefix: airline-demo
''',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 2'] = {
    'pipelineOrError': {
        'name': 'airline_demo_warehouse_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'local',
                'name': 'local',
                'runConfigYaml': '''resources:
  db_info:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  file_cache:
    config:
      target_folder: /tmp/dagster/airline_data/file_cache
  pyspark:
    config:
      spark_conf:
        spark:
          jars:
            packages: com.databricks:spark-avro_2.11:3.0.0,com.databricks:spark-redshift_2.11:2.0.1,com.databricks:spark-csv_2.11:1.5.0,org.postgresql:postgresql:42.2.5,org.apache.hadoop:hadoop-aws:2.6.5,com.amazonaws:aws-java-sdk:1.7.4
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
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 3'] = {
    'pipelineOrError': {
        'name': 'composition',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 4'] = {
    'pipelineOrError': {
        'name': 'daily_weather_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'development',
                'name': 'dev_weather_etl',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
  postgres_db:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  volume:
    config:
      mount_location: /tmp
solids:
  weather_etl:
    solids:
      download_weather_report_from_weather_api:
        inputs:
          epoch_date:
            value: 1514851200
      insert_weather_report_into_table:
        inputs:
          table_name:
            value: weather_staging
''',
                'solidSelection': [
                    'weather_etl'
                ]
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'production',
                'name': 'prod_weather_etl',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
      - POSTGRES_USERNAME
      - POSTGRES_PASSWORD
      - POSTGRES_HOST
      - POSTGRES_DB
  postgres_db:
    config:
      db_name:
        env: POSTGRES_DB
      hostname:
        env: POSTGRES_HOST
      password:
        env: POSTGRES_PASSWORD
      username:
        env: POSTGRES_USERNAME
  volume:
    config:
      mount_location: /tmp
solids:
  weather_etl:
    solids:
      download_weather_report_from_weather_api:
        inputs:
          epoch_date:
            value: 1514851200
      insert_weather_report_into_table:
        inputs:
          table_name:
            value: weather_staging
''',
                'solidSelection': [
                    'weather_etl'
                ]
            }
        ]
    }
}

snapshots['test_presets_on_examples 5'] = {
    'pipelineOrError': {
        'name': 'error_monster',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'errorable_mode',
                'name': 'passing',
                'runConfigYaml': '''resources:
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
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 6'] = {
    'pipelineOrError': {
        'name': 'event_ingest_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'default',
                'runConfigYaml': '''resources:
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
      application_jar: '{jar_path}'
      deploy_mode: client
      master_url: local[*]
      spark_conf:
        spark:
          app:
            name: test_app
''',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 7'] = {
    'pipelineOrError': {
        'name': 'generate_training_set_and_train_model',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'development',
                'name': 'dev_train_daily_bike_supply_model',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
  postgres_db:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  volume:
    config:
      mount_location: /tmp
solids:
  train_daily_bike_supply_model:
    inputs:
      trip_table_name: trips_staging
      weather_table_name: weather_staging
    solids:
      produce_training_set:
        config:
          memory_length: 1
      produce_weather_dataset:
        solids:
          load_entire_weather_table:
            config:
              subsets:
              - time
      train_lstm_model_and_upload_to_gcs:
        config:
          model_trainig_config:
            num_epochs: 200
          timeseries_train_test_breakpoint: 10
        inputs:
          bucket_name: dagster-scratch-ccdfe1e
      upload_training_set_to_gcs:
        inputs:
          bucket_name: dagster-scratch-ccdfe1e
          file_name: training_data
''',
                'solidSelection': [
                    'train_daily_bike_supply_model'
                ]
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'development',
                'name': 'dev_trip_etl',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
  postgres_db:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  volume:
    config:
      mount_location: /tmp
solids:
  trip_etl:
    solids:
      download_baybike_zipfile_from_url:
        inputs:
          base_url:
            value: https://s3.amazonaws.com/baywheels-data
          file_name:
            value: 202001-baywheels-tripdata.csv.zip
      insert_trip_data_into_table:
        inputs:
          table_name:
            value: trips_staging
      load_baybike_data_into_dataframe:
        inputs:
          target_csv_file_in_archive:
            value: 202001-baywheels-tripdata.csv
''',
                'solidSelection': [
                    'trip_etl'
                ]
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'development',
                'name': 'dev_weather_etl',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
  postgres_db:
    config:
      db_name: test
      hostname: localhost
      password: test
      username: test
  volume:
    config:
      mount_location: /tmp
solids:
  weather_etl:
    solids:
      download_weather_report_from_weather_api:
        inputs:
          epoch_date:
            value: 1514851200
      insert_weather_report_into_table:
        inputs:
          table_name:
            value: weather_staging
''',
                'solidSelection': [
                    'weather_etl'
                ]
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'production',
                'name': 'prod_train_daily_bike_supply_model',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
      - POSTGRES_USERNAME
      - POSTGRES_PASSWORD
      - POSTGRES_HOST
      - POSTGRES_DB
  postgres_db:
    config:
      db_name:
        env: POSTGRES_DB
      hostname:
        env: POSTGRES_HOST
      password:
        env: POSTGRES_PASSWORD
      username:
        env: POSTGRES_USERNAME
  volume:
    config:
      mount_location: /tmp
solids:
  train_daily_bike_supply_model:
    inputs:
      trip_table_name: trips_staging
      weather_table_name: weather_staging
    solids:
      produce_training_set:
        config:
          memory_length: 1
      produce_weather_dataset:
        solids:
          load_entire_weather_table:
            config:
              subsets:
              - time
      train_lstm_model_and_upload_to_gcs:
        config:
          model_trainig_config:
            num_epochs: 200
          timeseries_train_test_breakpoint: 10
        inputs:
          bucket_name: dagster-scratch-ccdfe1e
      upload_training_set_to_gcs:
        inputs:
          bucket_name: dagster-scratch-ccdfe1e
          file_name: training_data
''',
                'solidSelection': [
                    'train_daily_bike_supply_model'
                ]
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'production',
                'name': 'prod_trip_etl',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
      - POSTGRES_USERNAME
      - POSTGRES_PASSWORD
      - POSTGRES_HOST
      - POSTGRES_DB
  postgres_db:
    config:
      db_name:
        env: POSTGRES_DB
      hostname:
        env: POSTGRES_HOST
      password:
        env: POSTGRES_PASSWORD
      username:
        env: POSTGRES_USERNAME
  volume:
    config:
      mount_location: /tmp
solids:
  trip_etl:
    solids:
      download_baybike_zipfile_from_url:
        inputs:
          base_url:
            value: https://s3.amazonaws.com/baywheels-data
          file_name:
            value: 202001-baywheels-tripdata.csv.zip
      insert_trip_data_into_table:
        inputs:
          table_name:
            value: trips_staging
      load_baybike_data_into_dataframe:
        inputs:
          target_csv_file_in_archive:
            value: 202001-baywheels-tripdata.csv
''',
                'solidSelection': [
                    'trip_etl'
                ]
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'production',
                'name': 'prod_weather_etl',
                'runConfigYaml': '''resources:
  credentials_vault:
    config:
      environment_variable_names:
      - DARK_SKY_API_KEY
      - POSTGRES_USERNAME
      - POSTGRES_PASSWORD
      - POSTGRES_HOST
      - POSTGRES_DB
  postgres_db:
    config:
      db_name:
        env: POSTGRES_DB
      hostname:
        env: POSTGRES_HOST
      password:
        env: POSTGRES_PASSWORD
      username:
        env: POSTGRES_USERNAME
  volume:
    config:
      mount_location: /tmp
solids:
  weather_etl:
    solids:
      download_weather_report_from_weather_api:
        inputs:
          epoch_date:
            value: 1514851200
      insert_weather_report_into_table:
        inputs:
          table_name:
            value: weather_staging
''',
                'solidSelection': [
                    'weather_etl'
                ]
            }
        ]
    }
}

snapshots['test_presets_on_examples 8'] = {
    'pipelineOrError': {
        'name': 'jaffle_pipeline',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 9'] = {
    'pipelineOrError': {
        'name': 'log_spew',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 10'] = {
    'pipelineOrError': {
        'name': 'longitudinal_pipeline',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 11'] = {
    'pipelineOrError': {
        'name': 'many_events',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 12'] = {
    'pipelineOrError': {
        'name': 'pandas_hello_world_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'prod',
                'runConfigYaml': '''solids:
  mult_solid:
    inputs:
      num_df:
        csv:
          path: data/num_prod.csv
  sum_solid:
    inputs:
      num_df:
        csv:
          path: data/num_prod.csv
''',
                'solidSelection': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'test',
                'runConfigYaml': '''solids:
  mult_solid:
    inputs:
      num_df:
        csv:
          path: data/num.csv
  sum_solid:
    inputs:
      num_df:
        csv:
          path: data/num.csv
''',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 13'] = {
    'pipelineOrError': {
        'name': 'pandas_hello_world_pipeline_with_read_csv',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 14'] = {
    'pipelineOrError': {
        'name': 'simple_lakehouse_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'dev',
                'name': 'dev',
                'runConfigYaml': '''resources:
  filesystem:
    config:
      root: .
''',
                'solidSelection': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'prod',
                'name': 'prod',
                'runConfigYaml': '''resources:
  filesystem:
    config:
      root: .
''',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 15'] = {
    'pipelineOrError': {
        'name': 'simple_pyspark_sfo_weather_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'local',
                'name': 'local',
                'runConfigYaml': '''resources:
  pyspark:
    config:
      spark_conf:
        spark:
          jars:
            packages: com.databricks:spark-csv_2.11:1.5.0
solids:
  make_weather_samples:
    inputs:
      file_path: dagster_examples/simple_pyspark/sfo_q2_weather_sample.csv
storage:
  filesystem: null
''',
                'solidSelection': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'prod_databricks',
                'name': 'prod_databricks',
                'runConfigYaml': '''resources:
  pyspark_step_launcher:
    config:
      databricks_host: uksouth.azuredatabricks.net
      databricks_token:
        env: DATABRICKS_TOKEN
      local_pipeline_package_path: .
      run_config:
        cluster:
          new:
            nodes:
              node_types:
                node_type_id: Standard_DS3_v2
            size:
              num_workers: 1
            spark_version: 6.5.x-scala2.11
        run_name: dagster-tests
      staging_prefix: /dagster-databricks-tests
      storage:
        s3:
          access_key_key: aws-access-key
          secret_key_key: aws-secret-key
          secret_scope: dagster-databricks-tests
solids:
  make_weather_samples:
    inputs:
      file_path: s3://dagster-databricks-tests/sfo_q2_weather_fixed_header.txt
storage:
  s3:
    config:
      s3_bucket: dagster-databricks-tests
      s3_prefix: simple-pyspark
''',
                'solidSelection': None
            },
            {
                '__typename': 'PipelinePreset',
                'mode': 'prod_emr',
                'name': 'prod_emr',
                'runConfigYaml': '''resources:
  pyspark_step_launcher:
    config:
      cluster_id:
        env: EMR_CLUSTER_ID
      deploy_local_pipeline_package: true
      local_pipeline_package_path: .
      region_name: us-west-1
      spark_config:
        spark:
          jars:
            packages: com.databricks:spark-csv_2.11:1.5.0,org.apache.hadoop:hadoop-aws:2.6.5,com.amazonaws:aws-java-sdk:1.7.4
      staging_bucket: dagster-scratch-80542c2
solids:
  make_weather_samples:
    inputs:
      file_path: s3://dagster-airline-demo-source-data/sfo_q2_weather_fixed_header.txt
storage:
  s3:
    config:
      s3_bucket: dagster-scratch-80542c2
      s3_prefix: simple-pyspark
''',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 16'] = {
    'pipelineOrError': {
        'name': 'sleepy_pipeline',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'mode': 'default',
                'name': 'multi',
                'runConfigYaml': '''execution:
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
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_presets_on_examples 17'] = {
    'pipelineOrError': {
        'name': 'stdout_spew_pipeline',
        'presets': [
        ]
    }
}

snapshots['test_presets_on_examples 18'] = {
    'pipelineOrError': {
        'name': 'unreliable_pipeline',
        'presets': [
        ]
    }
}
