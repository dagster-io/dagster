from pyspark.sql import SparkSession

from dagster import resource, Field
from .types import DbInfo, PostgresConfigData, RedshiftConfigData
from .utils import (
    create_postgres_db_url,
    create_postgres_engine,
    create_redshift_db_url,
    create_redshift_engine,
)


@resource
def spark_session_local(_init_context):
    # Need two versions of this, one for test/local and one with a
    # configurable cluster
    spark = (
        SparkSession.builder.appName("AirlineDemo")
        .config(
            'spark.jars.packages',
            'com.databricks:spark-avro_2.11:3.0.0,'
            'com.databricks:spark-redshift_2.11:2.0.1,'
            'com.databricks:spark-csv_2.11:1.5.0,'
            'org.postgresql:postgresql:42.2.5,'
            'org.apache.hadoop:hadoop-aws:2.6.5,'
            'com.amazonaws:aws-java-sdk:1.7.4',
        )
        .getOrCreate()
    )
    return spark


@resource(config_field=Field(RedshiftConfigData))
def redshift_db_info_resource(init_context):
    db_url_jdbc = create_redshift_db_url(
        init_context.resource_config['redshift_username'],
        init_context.resource_config['redshift_password'],
        init_context.resource_config['redshift_hostname'],
        init_context.resource_config['redshift_db_name'],
    )

    db_url = create_redshift_db_url(
        init_context.resource_config['redshift_username'],
        init_context.resource_config['redshift_password'],
        init_context.resource_config['redshift_hostname'],
        init_context.resource_config['redshift_db_name'],
        jdbc=False,
    )

    s3_temp_dir = init_context.resource_config['s3_temp_dir']

    def _do_load(data_frame, table_name):
        data_frame.write.format('com.databricks.spark.redshift').option(
            'tempdir', s3_temp_dir
        ).mode('overwrite').jdbc(db_url_jdbc, table_name)

    return DbInfo(
        url=db_url,
        jdbc_url=db_url_jdbc,
        engine=create_redshift_engine(db_url),
        dialect='redshift',
        load_table=_do_load,
    )


@resource(config_field=Field(PostgresConfigData))
def postgres_db_info_resource(init_context):
    db_url_jdbc = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        init_context.resource_config['postgres_hostname'],
        init_context.resource_config['postgres_db_name'],
    )

    db_url = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        init_context.resource_config['postgres_hostname'],
        init_context.resource_config['postgres_db_name'],
        jdbc=False,
    )

    def _do_load(data_frame, table_name):
        data_frame.write.option('driver', 'org.postgresql.Driver').mode('overwrite').jdbc(
            db_url_jdbc, table_name
        )

    return DbInfo(
        url=db_url,
        jdbc_url=db_url_jdbc,
        engine=create_postgres_engine(db_url),
        dialect='postgres',
        load_table=_do_load,
    )
