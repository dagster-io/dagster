"""A fully fleshed out demo dagster repository with many configurable options."""

import os
import zipfile

from dagster import (
    Field,
    InputDefinition,
    OutputDefinition,
    solid,
    types,
)

from .types import (
    SparkDataFrameType,
)
from .utils import (
    mkdir_p,
)


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
            raise Exception('Missing table_name: required for materialization strategy "table"')

    @solid(
        name=name, outputs=[OutputDefinition(materialization_strategy_output_types[materialize])]
    )
    def sql_solid_fn(info):
        # n.b., we will eventually want to make this resources key configurable
        info.context.resources.db.execute(
            'create table :tablename as :statement', {
                'tablename': table_name,
                'statement': select_statement,
            }
        )
        return table_name

    return sql_solid_fn


@solid(
    name='thunk',
    config_field=Field(types.String),
)
def thunk(info):
    return info.config


@solid(
    name='download_from_s3',
    config_field=Field(
        types.ConfigDictionary(
            name='DownloadFromS3ConfigType',
            fields={
                # Probably want to make the region configuable too
                'bucket':
                Field(types.String, description=''),
                'key':
                Field(types.String, description=''),
                'skip_if_present':
                Field(types.Bool, description='', default_value=False, is_optional=True),
                'target_path':
                Field(types.String, description='', is_optional=True),
            }
        )
    )
)
def download_from_s3(info):
    bucket = info.config['bucket']
    key = info.config['key']
    target_path = (info.config.get('target_path') or key)

    if info.config['skip_if_present'] and os.path.isfile(target_path):
        return target_path

    if os.path.dirname(target_path):
        mkdir_p(os.path.dirname(target_path))

    info.context.resources.s3.download_file(bucket, key, target_path)
    return target_path


@solid(
    name='unzip_file',
    # config_field=Field(
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
        # InputDefinition(
        #     'destination_dir',
        #     types.String,
        #     description='',
        # ),
    ],
    config_field=Field(
        types.ConfigDictionary(
            name='UnzipFileConfigType',
            fields={
                'skip_if_present':
                Field(types.Bool, description='', default_value=False, is_optional=True),
            }
        )
    )
)
def unzip_file(
    info,
    archive_path,
    archive_member,
    # destination_dir=None
):
    # FIXME
    # archive_path = info.config['archive_path']
    # archive_member = info.config['archive_member']
    destination_dir = (
        # info.config['destination_dir'] or
        os.path.dirname(archive_path)
    )

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        if archive_member is not None:
            target_path = os.path.join(destination_dir, archive_member)
            if not (
                info.config['skip_if_present'] and
                (os.path.isfile(target_path) or os.path.isdir(target_path))
            ):
                zip_ref.extract(archive_member, destination_dir)
        else:
            if not (info.config['skip_if_present'] and os.path.isdir(target_path)):
                zip_ref.extractall(destination_dir)
        return target_path


@solid(
    name='ingest_csv_to_spark',
    config_field=Field(
        types.ConfigDictionary(
            name='IngestCsvToSparkConfigType',
            fields={
                'input_csv':
                Field(types.String, description='', default_value='', is_optional=True),
            }
        )
    ),
    inputs=[InputDefinition(
        'input_csv',
        types.String,
        description='',
    )],
    outputs=[OutputDefinition(SparkDataFrameType)]
)
def ingest_csv_to_spark(info, input_csv=None):
    data_frame = (
        info.context.resources.spark.read.format('csv').options(
            header='true',
            # inferSchema='true',
        ).load(input_csv or info.config['input_csv'])
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
    # config_field=Field(
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
    name='load_data_to_database_from_spark',
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame to load into Redshift.',
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
    config_field=Field(
        types.ConfigDictionary(
            name='BatchLoadDataToRedshiftFromSparkConfigType',
            fields={
                'table_name': Field(types.String, description=''),
            }
        )
    )
)
def load_data_to_database_from_spark(info, data_frame):
    # Move this to context, config at that level
    db_dialect = info.context.resources.db_dialect
    if db_dialect == 'redshift':
        data_frame.write \
        .format('com.databricks.spark.redshift') \
        .option('tempdir', info.context.resources.redshift_s3_temp_dir) \
        .mode('overwrite') \
        .jdbc(
            info.context.resources.db_url,
            info.config['table_name'],
        ) #\
        # .save()
    elif db_dialect == 'postgres':
        data_frame.write \
        .option('driver', 'org.postgresql.Driver') \
        .mode('overwrite') \
        .jdbc(
            info.context.resources.db_url,
            info.config['table_name'],
        ) #\
        # .save()
    else:
        raise NotImplementedError(
            'No implementation for db_dialect "{db_dialect}"'.format(db_dialect=db_dialect)
        )
    return data_frame


@solid(
    name='subsample_spark_dataset',
    description='Subsample a spark dataset.',
    config_field=Field(
        types.ConfigDictionary(
            name='SubsampleSparkDataFrameConfigType',
            fields={
                'subsample_pct': Field(types.Int, description=''),
            }
        )
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
    config_field=Field(
        types.ConfigDictionary(
            name='JoinSparkDataFramesConfigType',
            fields={
                # Probably want to make the region configuable too
                'on_left':
                Field(types.String, description='', default_value='id', is_optional=True),
                'on_right':
                Field(types.String, description='', default_value='id', is_optional=True),
                'how': Field(types.String, description='', default_value='inner', is_optional=True),
            }
        )
    )
)
def join_spark_data_frames(info, left_data_frame, right_data_frame):
    return left_data_frame.join(
        right_data_frame,
        on=(
            getattr(left_data_frame,
                    info.config.on_left) == getattr(right_data_frame, info.config.on_right)
        ),
        how=info.config.how
    )
