"""A fully fleshed out demo dagster repository with many configurable options."""

import logging
import os
import zipfile

from collections import namedtuple

import boto3
import sqlalchemy

from pyspark.sql import (
    DataFrame,
    SparkSession,
)

from dagster import (
    ConfigDefinition,
    DependencyDefinition,
    ExecutionContext,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    solid,
    SolidInstance,
    types,
)


AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'redshift'),
)

SparkDataFrameType = types.PythonObjectType(
    'SparkDataFrameType',
    python_type=DataFrame,
    description='A Pyspark data frame.',
)

# SqlAlchemyQueryType = types.PythonObjectType(
#     'SqlAlchemyQueryType',
#     python_type=sqlalchemy.orm.query.Query,
#     description='A SQLAlchemy query.',
# )

# SqlAlchemySubqueryType = types.PythonObjectType(
#     'SqlAlchemySubqueryType',
#     python_type=sqlalchemy.sql.expression.Alias,
#     description='A SQLAlchemy subquery',
# )

# SqlAlchemyResultProxyType = types.PythonObjectType(
#     'SqlAlchemyResultProxyType',
#     python_type=sqlalchemy.engine.ResultProxy,
#     description='A SQLAlchemy result proxy',
# )

# need a sql context w a sqlalchemy engine
def sql_solid(name, select_statement, materialize, table_name=None):
    materialization_strategy_output_types = {
        'table': types.String,
        # 'view': types.String,
        # 'query': SqlAlchemyQueryType,
        # 'subquery': SqlAlchemySubqueryType,
        # 'result_proxy': SqlAlchemyResultProxyType,
        # could also materialize as a Pandas table, as a Spark table, as an intermediate file, etc.
    }

    if materialize not in materialization_strategy_output_types:
        raise Exception(
            "Invalid materialization strategy {materialize}, must "
            "be one of {materialization_strategies}".format(
                materialize=materialize,
                materialization_strategies=materialization_strategy_output_types.keys()
            )
        )

    if materialize == 'table':
        if table_name is None:
            raise Exception("Missing table_name")

    @solid(
        name=name,
        outputs=[OutputDefinition(materialization_strategy_output_types[materialize])]
    )
    def sql_solid_fn(info):
        # n.b., we will eventually want to make this resources key configurable
        info.context.resources.db.execute(
            'create table :tablename as :statement', {
                'tablename': table_name,
                'statement': select_statement,
            })
        return table_name

    return sql_solid_fn


def _create_spark_session_local():
    # Need two versions of this, one for test/local and one with a
    # configurable cluster
    spark = SparkSession.builder.appName("AirlineDemo").getOrCreate()
    return spark


def _create_s3_session():
    s3 = boto3.resource('s3')
    return s3


def _create_redshift_engine(username, password, hostname, db_name):
    db_url = (
        "redshift_psycopg2://{username}:{password}@{hostname}:5439/{db_name}".format(
            username=username,
            password=password,
            hostname=hostname,
            db_name=db_name,
        )
    )
    return sqlalchemy.create_engine(db_url)


def _create_postgres_engine(username, password, hostname, db_name):
    db_url = (
        "postgresql://{username}:{password}@{hostname}:5432/{db_name}".format(
            username=username,
            password=password,
            hostname=hostname,
            db_name=db_name,
        )
    )
    return sqlalchemy.create_engine(db_url)


test_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                _create_spark_session_local(), # FIXME
                _create_s3_session(),
                _create_redshift_engine(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_hostname'],
                    info.config('redshift_db_name'),
                ),
            )
        )
    )
)


local_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                _create_spark_session_local(),
                _create_s3_session(),
                _create_postgres_engine(
                    info.config['postgres_username'],
                    info.config['postgres_password'],
                    info.config['postgres_cluster_dns'],
                    info.config('postgres_db_name'),
                ),
            )
        )
    )
)


cloud_context = PipelineContextDefinition(
    context_fn=(
        lambda info: ExecutionContext.console_logging(
            log_level=logging.DEBUG,
            resources=AirlineDemoResources(
                _create_spark_session_local(), # FIXME
                _create_s3_session(),
                _create_redshift_engine(
                    info.config['redshift_username'],
                    info.config['redshift_password'],
                    info.config['redshift_cluster_dns'],
                    info.config('redshift_db_name'),
                ),
            )
        )
    )
)


@solid(
    name='download_from_s3',
    config_def=ConfigDefinition(
        types.ConfigDictionary(name='DownloadFromS3ConfigType', fields={
            # Probably want to make the region configuable too
            'bucket': Field(types.String, description=''),
            'key': Field(types.String, description=''),
            'target_path': Field(types.String, description=''),
        })
    ))
def download_from_s3(info):
    bucket = info.config['bucket']
    key = info.config['key']
    target_path = info.config.get('target_path') or key
    info.s3.meta.client.download_file(bucket, key, target_path)
    return target_path

@solid(
    name='unzip_file',
    # config_def=ConfigDefinition(
    #     types.ConfigDictionary(name='UnzipFileConfigType', fields={
    #         ' archive_path': Field(types.String, description=''),
    #         'archive_member': Field(types.String, description=''),
    #         'destination_dir': Field(types.String, description=''),
    #     })
    # ),
    inputs=[
        InputDefinition(
            'archive_path',
            types.String,
            description='',
        ),
        InputDefinition(
            'archive_member',
            types.String,
            description='',
        ),
        InputDefinition(
            'destination_dir',
            types.String,
            description='',
        ),

    ]
)
def unzip_file(info, archive_path, archive_member=None, destination_dir=None):
    # FIXME
    archive_path = info.config['archive_path']
    archive_member = info.config['archive_member']
    destination_dir = info.config['destination_dir'] or os.path.dirname(archive_path)

    zip_ref = zipfile.ZipFile(archive_path, 'r')

    if archive_member is not None:
        zip_ref.extract(archive_member, destination_dir)
    else:
        zip_ref.extractall(destination_dir)
    zip_ref.close()


@solid(
    name='ingest_csv_to_spark',
    config_def=ConfigDefinition(
        types.ConfigDictionary(name='IngestCsvToSparkConfigType', fields={
            'input_csv': Field(types.String, description=''),
        })
    ),
    inputs=InputDefinition(
        'input_csv',
        types.String,
        description=''
    )
    outputs=[OutputDefinition(SparkDataFrameType)]
)
def ingest_csv_to_spark(info, input_csv=None):
    data_frame = (
        info.context.resources.spark
        .read
        .format('csv')
        .options(
            header='true',
            # inferSchema='true',
        )
        .load(input_csv or info.config['input_csv'])
    )
    return data_frame


def replace_values_spark(data_frame, old, new, columns=None):
    if columns is None:
        data_frame.na.replace(old, new)
        return data_frame
    # FIXME handle selecting certain columns
    return data_frame


def fix_na_spark(data_frame, na_value, columns=None):
    return replace_values_spark(data_frame, na_value, None, columns=columns)


@solid(
    name='normalize_weather_na_values',
    description="Normalizes the given NA values by replacing them with None",
    # FIXME can this be optional
    # config_def=ConfigDefinition(
    #     types.String,
    #     # description='The string NA value to normalize to None.'
    # ),
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame containing NA values to normalize.',
        )
    ],
)
def normalize_weather_na_values(info, data_frame):
    return fix_na_spark(data_frame, 'M')


@solid(
    name='batch_load_data_to_redshift_from_spark',
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame to load into Redshift.',
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
    config_def=ConfigDefinition(
        types.ConfigDictionary(name='BatchLoadDataToRedshiftFromSparkConfigType', fields={
            'db_url': Field(types.String, description=''),
            'table_name': Field(types.String, description=''),
        })
    ),
)            # "jdbc:redshift://redshifthost:5439/database?user=username&password=pass") \
def batch_load_data_to_redshift_from_spark(info, data_frame):
    data_frame.write \
        .format("com.databricks.spark.redshift") \
        .option(
            "url",
            info.config['db_url']) \
        .option("dbtable", info.config['table_name']) \
        .mode("error") \
        .save()
    return data_frame


@solid(
    name='batch_load_data_to_postgres_from_spark',
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame to load into Postgres.',
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)]
)
def batch_load_data_to_postgres_from_spark(info, data_frame):
    # https://github.com/databricks/spark-redshift
    return data_frame


@solid(
    name='subsample_spark_dataset',
    description='Subsample a spark dataset.',
    config_def=ConfigDefinition(
        types.ConfigDictionary(name='SubsampleSparkDataFrameConfigType', fields={
            'subsample_pct': Field(types.Int, description=''),
        })
        # description='The integer percentage of rows to sample from the input dataset.'
    ),
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame to subsample.',
        )
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            # description='A pyspark DataFrame containing a subsample of the input rows.',
        )
    ]
)
def subsample_spark_dataset(info, data_frame):
    return data_frame.sample(False, info.config['subsample_pct'] / 100.)


@solid(
    name='join_spark_data_frames',
    inputs=[
        InputDefinition(
            'left_data_frame',
            SparkDataFrameType,
            description='The left DataFrame to join.',
        ),
        InputDefinition(
            'right_data_frame',
            SparkDataFrameType,
            description='The right DataFrame to join.',
        ),
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            # description='A pyspark DataFrame containing a subsample of the input rows.',
        )
    ],
)
def join_spark_data_frames(info, left_data_frame, right_data_frame):
    # FIXME
    return left_data_frame


def define_airline_demo_spark_ingest_pipeline():
    context_definitions = {
        'test': test_context,
        'local': local_context,
        'cloud': cloud_context,
    }

    solids = [
        download_from_s3,
        ingest_csv_to_spark,
        batch_load_data_to_redshift_from_spark,
        subsample_spark_dataset,
        normalize_weather_na_values,
        join_spark_data_frames,
    ]

    dependencies = {
        SolidInstance('download_from_s3', alias='download_april_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_may_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_june_on_time_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_sfo_weather'): {},
        SolidInstance('download_from_s3', alias='download_q2_coupon_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_market_data'): {},
        SolidInstance('download_from_s3', alias='download_q2_ticket_data'): {},

        SolidInstance('unzip_file', alias='unzip_april_on_time_data'): {
            'archive_path': DependencyDefinition('download_april_on_time_data')
        },
        SolidInstance('unzip_file', alias='unzip_may_on_time_data'): {
            'archive_path': DependencyDefinition('download_may_on_time_data')
        },
        SolidInstance('unzip_file', alias='unzip_june_on_time_data'): {},
            'archive_path': DependencyDefinition('download_june_on_time_data')
        SolidInstance('unzip_file', alias='unzip_q2_sfo_weather'): {
            'archive_path': DependencyDefinition('download_q2_sfo_weather')
        },
        SolidInstance('unzip_file', alias='unzip_q2_coupon_data'): {
# FIXME
        },
        SolidInstance('unzip_file', alias='unzip_q2_market_data'): {
# FIXME
        },
        SolidInstance('unzip_file', alias='unzip_q2_ticket_data'): {
# FIXME
        },

        SolidInstance('ingest_csv_to_spark', alias='ingest_april_on_time_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_may_on_time_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_june_on_time_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_april_sfo_weather'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_may_sfo_weather'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_june_sfo_weather'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_coupon_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_market_data'): {},
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_ticket_data'): {},
        SolidInstance('subsample_spark_dataset', alias='subsample_april_on_time_data'): {
            'data_frame': DependencyDefinition('ingest_april_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_may_on_time_data'): {
            'data_frame': DependencyDefinition('ingest_may_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_june_on_time_data'): {
            'data_frame': DependencyDefinition('ingest_june_on_time_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_april_sfo_weather'): {
            'data_frame': DependencyDefinition('ingest_april_sfo_weather'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_may_sfo_weather'): {
            'data_frame': DependencyDefinition('ingest_may_sfo_weather'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_june_sfo_weather'): {
            'data_frame': DependencyDefinition('ingest_june_sfo_weather'),
        },
        SolidInstance('normalize_weather_na_values', alias='normalize_april_weather_na_values'): {
            'data_frame': DependencyDefinition('subsample_april_sfo_weather'),
        },
        SolidInstance('normalize_weather_na_values', alias='normalize_may_weather_na_values'): {
            'data_frame': DependencyDefinition('subsample_may_sfo_weather'),
        },
        SolidInstance('normalize_weather_na_values', alias='normalize_june_weather_na_values'): {
            'data_frame': DependencyDefinition('subsample_june_sfo_weather'),
        },
        SolidInstance('join_spark_data_frames', alias='join_april_weather_to_on_time_data'): {
            'left_data_frame': DependencyDefinition('subsample_april_on_time_data'),
            'right_data_frame': DependencyDefinition('normalize_april_weather_na_values'),
        },
        SolidInstance('join_spark_data_frames', alias='join_may_weather_to_on_time_data'): {
            'left_data_frame': DependencyDefinition('subsample_may_on_time_data'),
            'right_data_frame': DependencyDefinition('normalize_may_weather_na_values'),
        },
        SolidInstance('join_spark_data_frames', alias='join_june_weather_to_on_time_data'): {
            'left_data_frame': DependencyDefinition('subsample_june_on_time_data'),
            'right_data_frame': DependencyDefinition('normalize_june_weather_na_values'),
        },
        SolidInstance(
            'batch_load_data_to_redshift_from_spark',
            alias='load_april_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_april_weather_to_on_time_data'),
        },
        SolidInstance(
            'batch_load_data_to_redshift_from_spark',
            alias='load_may_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_may_weather_to_on_time_data'),
        },
        SolidInstance(
            'batch_load_data_to_redshift_from_spark',
            alias='load_june_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_june_weather_to_on_time_data'),
        },
        SolidInstance('batch_load_data_to_redshift_from_spark', alias='load_q2_coupon_data'): {
            'data_frame': DependencyDefinition('ingest_q2_coupon_data'),
        },
        SolidInstance('batch_load_data_to_redshift_from_spark', alias='load_q2_market_data'): {
            'data_frame': DependencyDefinition('ingest_q2_market_data'),
        },
        SolidInstance('batch_load_data_to_redshift_from_spark', alias='load_q2_ticket_data'): {
            'data_frame': DependencyDefinition('ingest_q2_ticket_data'),
        },
        SolidInstance(
            'batch_load_data_to_postgres_from_spark',
            alias='load_april_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_april_weather_to_on_time_data'),
        },
        SolidInstance(
            'batch_load_data_to_postgres_from_spark',
            alias='load_may_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_may_weather_to_on_time_data'),
        },
        SolidInstance(
            'batch_load_data_to_postgres_from_spark',
            alias='load_june_weather_and_on_time_data'
        ): {
            'data_frame': DependencyDefinition('join_june_weather_to_on_time_data'),
        },
        SolidInstance(
            'batch_load_data_to_postgres_from_spark',
            alias='load_q2_coupon_data'
        ): {
            'data_frame': DependencyDefinition('ingest_q2_coupon_data'),
        },
        SolidInstance(
            'batch_load_data_to_postgres_from_spark',
            alias='load_q2_market_data'
        ): {
            'data_frame': DependencyDefinition('ingest_q2_market_data'),
        },
        SolidInstance(
            'batch_load_data_to_postgres_from_spark', 
            alias='load_q2_ticket_data'
        ): {
            'data_frame': DependencyDefinition('ingest_q2_ticket_data'),
        },
    }

    return PipelineDefinition(
        name="airline_demo_spark_ingest_pipeline",
        solids=solids,
        dependencies=dependencies,
        context_definitions=context_definitions,
    )

def define_airline_demo_warehouse_pipeline():
    context_definitions = {
        'test': test_context,
        'local': local_context,
        'cloud': cloud_context,
    }

    return PipelineDefinition(
        name="airline_demo_warehouse_pipeline",
        solids=[
        ],
        dependencies={
        },
        context_definitions=context_definitions,
    )


def define_repo():
    return RepositoryDefinition(
        name='airline_demo_repo',
        pipeline_dict={
            'airline_demo_spark_ingest_pipeline':
            define_airline_demo_spark_ingest_pipeline,
            'airline_demo_warehouse_pipeline':
            define_airline_demo_warehouse_pipeline,
        })
