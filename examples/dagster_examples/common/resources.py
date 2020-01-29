from collections import namedtuple

import sqlalchemy

from dagster import Field, resource

DbInfo = namedtuple('DbInfo', 'engine url jdbc_url dialect load_table host db_name')


def create_redshift_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username, password=password, hostname=hostname, db_name=db_name
            )
        )
    else:
        db_url = "redshift_psycopg2://{username}:{password}@{hostname}:5439/{db_name}".format(
            username=username, password=password, hostname=hostname, db_name=db_name
        )
    return db_url


def create_redshift_engine(db_url):
    return sqlalchemy.create_engine(db_url)


def create_postgres_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username, password=password, hostname=hostname, db_name=db_name
            )
        )
    else:
        db_url = 'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
            username=username, password=password, hostname=hostname, db_name=db_name
        )
    return db_url


def create_postgres_engine(db_url):
    return sqlalchemy.create_engine(db_url)


@resource(
    {
        'redshift_username': Field(str),
        'redshift_password': Field(str),
        'redshift_hostname': Field(str),
        'redshift_db_name': Field(str),
        's3_temp_dir': Field(str),
    }
)
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


@resource(
    {
        'postgres_username': Field(str),
        'postgres_password': Field(str),
        'postgres_hostname': Field(str),
        'postgres_db_name': Field(str),
    }
)
def postgres_db_info_resource(init_context):
    host = init_context.resource_config['postgres_hostname']
    db_name = init_context.resource_config['postgres_db_name']
    db_url_jdbc = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        host,
        db_name,
    )

    db_url = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        host,
        db_name,
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
        host=host,
        db_name=db_name,
    )
