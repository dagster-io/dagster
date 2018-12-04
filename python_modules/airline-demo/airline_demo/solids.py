'''A fully fleshed out demo dagster repository with many configurable options.'''

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
def create_sql_solid(name, select_statement, materialization_strategy, table_name=None):
    '''Return a new solid that executes and materializes a SQL select statement.

    Args:
        name (str): The name of the new solid.
        select_statement (str): The select statement to execute.
        materialization_strategy (str): Must be 'table', the only currently supported
            materialization strategy. If 'table', the kwarg `table_name` must also be passed.

    Kwargs:
        table_name (str): THe name of the new table to create, if the materialization strategy
            is 'table'.

    Returns:
        function:
            The new SQL solid.
    '''
    materialization_strategy_output_types = {  # pylint:disable=C0103
        'table': types.String,
        # 'view': types.String,
        # 'query': SqlAlchemyQueryType,
        # 'subquery': SqlAlchemySubqueryType,
        # 'result_proxy': SqlAlchemyResultProxyType,
        # could also materialize as a Pandas table, as a Spark table, as an intermediate file, etc.
    }

    if materialization_strategy not in materialization_strategy_output_types:
        raise Exception(
            'Invalid materialization strategy {materialization_strategy}, must '
            'be one of {materialization_strategies}'.format(
                materialization_strategy=materialization_strategy,
                materialization_strategies=str(list(materialization_strategy_output_types.keys()))
            )
        )

    if materialization_strategy == 'table':
        if table_name is None:
            raise Exception('Missing table_name: required for materialization strategy \'table\'')

    @solid(
        name=name,
        outputs=[
            OutputDefinition(
                materialization_strategy_output_types[materialization_strategy],
                description='The materialized SQL statement. If the materialization_strategy is '
                '\'table\', this is the string name of the new table created by the solid.'
            )
        ]
    )
    def sql_solid_fn(info):
        '''Inner function defining the new solid.

        Args:
            info (ExpectationExecutionInfo): Must expose a `db` resource with an `execute` method,
                like a SQLAlchemy engine, that can execute raw SQL against a database.

        Returns:
            str:
                The table name of the newly materialized SQL select statement.
        '''
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
    config_field=Field(types.String, description='The string value to output.'),
    description='No-op solid that simply outputs its single string config value.',
    outputs=[OutputDefinition(types.String, description='The string passed in as config.')]
)
def thunk(info):
    '''Output the config vakue.

    Especially useful when constructing DAGs with root nodes that take inputs which might in
    other dags come from upstream solids.

    Args:
        info (ExpectationExecutionInfo)

    Returns:
        str;
            The config value passed to the solid.
    '''
    return info.config


@solid(
    name='download_from_s3',
    config_field=Field(
        types.ConfigDictionary(
            name='DownloadFromS3ConfigType',
            fields={
                # Probably want to make the region configuable too
                'bucket':
                Field(types.String, description='The S3 bucket in which to look for the key.'),
                'key':
                Field(types.String, description='The key to download.'),
                'skip_if_present':
                Field(
                    types.Bool,
                    description='If True, and a file already exists at the path described by the '
                    'target_path config value, if present, or the key, then the solid will no-op.',
                    default_value=False,
                    is_optional=True
                ),
                'target_path':
                Field(
                    types.String,
                    description='If present, specifies the path at which to download the object.',
                    is_optional=True
                ),
            }
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(types.String, description='The path to the downloaded object.')]
)
def download_from_s3(info):
    '''Download an object from s3.
        
    Args:
        info (ExpectationExecutionInfo): Must expose a boto3 S3 client as its `s3` resource.

    Returns:
        str:
            The path to the downloaded object.
    '''
    bucket = info.config['bucket']
    key = info.config['key']
    target_path = (info.config.get('target_path') or key)

    if info.config['skip_if_present'] and os.path.isfile(target_path):
        info.context.info(
            'Skipping download, file already present at {target_path}'.format(
                target_path=target_path
            )
        )
        return target_path

    if os.path.dirname(target_path):
        mkdir_p(os.path.dirname(target_path))

    info.context.resources.s3.download_file(bucket, key, target_path)
    return target_path


@solid(
    name='unzip_file',
    # config_field=Field(
    #     types.ConfigDictionary(name='UnzipFileConfigType', fields={
    #         'archive_path': Field(types.String, description=''),
    #         'archive_member': Field(types.String, description=''),
    #         'destination_dir': Field(types.String, description=''),
    #     })
    # ),
    inputs=[
        InputDefinition(
            'archive_path',
            types.String,
            description='The path to the archive.',
        ),
        InputDefinition(
            'archive_member',
            types.String,
            description='The archive member to extract.',
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
                Field(
                    types.Bool,
                    description='If True, and a file already exists at the path to which the '
                    'archive member would be unzipped, then the solid will no-op',
                    default_value=False,
                    is_optional=True
                ),
            }
        )
    ),
    description='Extracts an archive member from a zip archive.',
    outputs=[
        OutputDefinition(types.String, description='The path to the unzipped archive member.')
    ],
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
            is_file = os.path.isfile(target_path)
            is_dir = os.path.isdir(target_path)
            if not (info.config['skip_if_present'] and (is_file or is_dir)):
                zip_ref.extract(archive_member, destination_dir)
            else:
                if is_file:
                    info.context.info(
                        'Skipping unarchive of {archive_member} from {archive_path}, '
                        'file already present at {target_path}'.format(
                            archive_member=archive_member,
                            archive_path=archive_path,
                            target_path=target_path
                        )
                    )
                if is_dir:
                    info.context.info(
                        'Skipping unarchive of {archive_member} from {archive_path}, '
                        'directory already present at {target_path}'.format(
                            archive_member=archive_member,
                            archive_path=archive_path,
                            target_path=target_path
                        )
                    )
        else:
            if not (info.config['skip_if_present'] and is_dir):
                zip_ref.extractall(destination_dir)
            else:
                info.context.info(
                    'Skipping unarchive of {archive_path}, directory already present '
                    'at {target_path}'.format(archive_path=archive_path, target_path=target_path)
                )
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
def normalize_weather_na_values(_info, data_frame):
    return fix_na_spark(data_frame, 'M')


@solid(
    name='load_data_to_database_from_spark',
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame to load into the database.',
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
    config_field=Field(
        types.ConfigDictionary(
            name='BatchLoadDataToDatabaseFromSparkConfigType',
            fields={
                'table_name': Field(types.String, description=''),
            }
        )
    )
)
def load_data_to_database_from_spark(info, data_frame):
    # Move this to context, config at that level
    info.context.resources.db_load(data_frame, info.config['table_name'], info.context.resources)
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
                    info.config['on_left']) == getattr(right_data_frame, info.config['on_right'])
        ),
        how=info.config['how']
    )
