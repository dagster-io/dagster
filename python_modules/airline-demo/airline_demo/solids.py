'''A fully fleshed out demo dagster repository with many configurable options.'''

import os
import zipfile

from sqlalchemy import text
from stringcase import snakecase

from dagster import (
    Field,
    InputDefinition,
    OutputDefinition,
    Result,
    solid,
    SolidDefinition,
    types,
)
from dagstermill import define_dagstermill_solid

from .types import (
    SparkDataFrameType,
    SqlAlchemyEngineType,
    SqlTableName,
)
from .utils import (
    mkdir_p,
)


def _notebook_path(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notebooks', name)


def notebook_solid(name, inputs, outputs):
    return define_dagstermill_solid(
        snakecase(name.split('.ipynb')[0]),
        _notebook_path(name),
        inputs,
        outputs,
    )


# need a sql context w a sqlalchemy engine
def sql_solid(name, select_statement, materialization_strategy, table_name=None, inputs=None):
    '''Return a new solid that executes and materializes a SQL select statement.

    Args:
        name (str): The name of the new solid.
        select_statement (str): The select statement to execute.
        materialization_strategy (str): Must be 'table', the only currently supported
            materialization strategy. If 'table', the kwarg `table_name` must also be passed.
    Kwargs:
        table_name (str): THe name of the new table to create, if the materialization strategy
            is 'table'. Default: None.
        inputs (list[InputDefinition]): Inputs, if any, for the new solid. Default: None.

    Returns:
        function:
            The new SQL solid.
    '''
    if inputs is None:
        inputs = []

    materialization_strategy_output_types = {  # pylint:disable=C0103
        'table': SqlTableName,
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

    output_description = (
        'The string name of the new table created by the solid'
        if materialization_strategy == 'table' else
        'The materialized SQL statement. If the materialization_strategy is '
        '\'table\', this is the string name of the new table created by the solid.'
    )

    description = '''This solid executes the following SQL statement:
    {select_statement}'''.format(select_statement=select_statement)

    def transform_fn(info, _inputs):
        '''Inner function defining the new solid.

        Args:
            info (ExpectationExecutionInfo): Must expose a `db` resource with an `execute` method,
                like a SQLAlchemy engine, that can execute raw SQL against a database.

        Returns:
            str:
                The table name of the newly materialized SQL select statement.
        '''
        # n.b., we will eventually want to make this resources key configurable
        sql_statement = (
            'drop table if exists {table_name}; '
            'create table {table_name} as {select_statement};'
        ).format(
            table_name=table_name,
            select_statement=select_statement,
        )

        info.context.info(
            'Executing sql statement:\n{sql_statement}'.format(sql_statement=sql_statement)
        )
        info.context.resources.db_engine.execute(text(sql_statement))
        yield Result(value=table_name, output_name='result')

    return SolidDefinition(
        name=name,
        inputs=inputs,
        outputs=[
            OutputDefinition(
                materialization_strategy_output_types[materialization_strategy],
                description=output_description
            )
        ],
        transform_fn=transform_fn,
        description=description,
        metadata={
            'kind': 'sql',
        },
    )


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
    name='thunk_database_engine',
    outputs=[OutputDefinition(SqlAlchemyEngineType, description='The db resource.')]
)
def thunk_database_engine(info):
    """Returns the db resource as its output.

    Why? Because we don't currently have a good way to pass contexts around between execution
    threads. So in order to get a database engine into a Jupyter notebook, we need to serialize
    it and pass it along.
    """
    return info.context.resources.db


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
                    types.Path,
                    description='If present, specifies the path at which to download the object.',
                    is_optional=True
                ),
            }
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(types.Path, description='The path to the downloaded object.')]
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
    name='upload_to_s3',
    config_field=Field(
        types.ConfigDictionary(
            name='UploadToS3ConfigType',
            fields={
                # Probably want to make the region configuable too
                'bucket':
                Field(types.String, description='The S3 bucket to which to upload the file.'),
                'key':
                Field(types.String, description='The key to which to upload the file.'),
                'kwargs':
                Field(
                    types.Dict,
                    description='Kwargs to pass through to the S3 client',
                    is_optional=True,
                )
            }
        )
    ),
    inputs=[
        InputDefinition(
            'file_path',
            types.Path,
            description='The path of the file to upload.',
        ),
    ],
    description='Uploads a file to S3.',
    outputs=[
        OutputDefinition(
            types.String,
            description='The bucket to which the file was uploaded.',
            name='bucket',
        ),
        OutputDefinition(
            types.String,
            description='The key to which the file was uploaded.',
            name='key',
        ),
    ],
)
def upload_to_s3(info, file_path):
    '''Upload a file to s3.
        
    Args:
        info (ExpectationExecutionInfo): Must expose a boto3 S3 client as its `s3` resource.

    Returns:
        (str, str):
            The bucket and key to which the file was uploaded.
    '''
    bucket = info.config['bucket']
    key = info.config['key']

    with open(file_path, 'rb') as fd:
        info.context.resources.s3.put_object(
            Bucket=bucket, Body=fd, Key=key, **(info.config.get('kwargs') or {})
        )
    yield Result(bucket, 'bucket')
    yield Result(key, 'key')


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
            types.Path,
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
    outputs=[OutputDefinition(types.Path, description='The path to the unzipped archive member.')],
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
                'input_csv': Field(types.Path, description='', default_value='', is_optional=True),
            }
        )
    ),
    inputs=[InputDefinition(
        'input_csv',
        types.Path,
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


def rename_spark_dataframe_columns(data_frame, fn):
    return data_frame.toDF(*[fn(c) for c in data_frame.columns])


@solid(
    name='prefix_column_names',
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The data frame whose columns should be prefixed'
        ),
    ],
    config_field=Field(types.String),
    outputs=[OutputDefinition(SparkDataFrameType)]
)
def prefix_column_names(info, data_frame):
    return rename_spark_dataframe_columns(
        data_frame, lambda c: '{prefix}{c}'.format(prefix=info.config, c=c)
    )


@solid(
    name='canonicalize_column_names',
    inputs=[
        InputDefinition(
            'data_frame', SparkDataFrameType, description='The data frame to canonicalize'
        ),
    ],
    outputs=[OutputDefinition(SparkDataFrameType)]
)
def canonicalize_column_names(_info, data_frame):
    return rename_spark_dataframe_columns(data_frame, lambda c: c.lower())


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


@solid(
    name='union_spark_data_frames',
    inputs=[
        InputDefinition(
            'left_data_frame',
            SparkDataFrameType,
            description='The left DataFrame to union.',
        ),
        InputDefinition(
            'right_data_frame',
            SparkDataFrameType,
            description='The right DataFrame to union.',
        ),
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            description='A pyspark DataFrame containing the union of the input data frames.',
        )
    ],
)
def union_spark_data_frames(_info, left_data_frame, right_data_frame):
    return left_data_frame.union(right_data_frame)


q2_sfo_outbound_flights = sql_solid(
    'q2_sfo_outbound_flights',
    '''
    select * from q2_on_time_data
    where origin = 'SFO'
    ''',
    'table',
    table_name='q2_sfo_outbound_flights',
)

average_sfo_outbound_avg_delays_by_destination = sql_solid(
    'average_sfo_outbound_avg_delays_by_destination',
    '''
    select
        cast(cast(arrdelay as float) as integer) as arrival_delay,
        cast(cast(depdelay as float) as integer) as departure_delay,
        origin,
        dest as destination
    from q2_sfo_outbound_flights
    ''',
    'table',
    table_name='average_sfo_outbound_avg_delays_by_destination',
    inputs=[InputDefinition('q2_sfo_outbound_flights', dagster_type=SqlTableName)]
)

ticket_prices_with_average_delays = sql_solid(
    'tickets_with_destination',
    '''
    select
        tickets.*,
        coupons.dest,
        coupons.destairportid,
        coupons.destairportseqid, coupons.destcitymarketid,
        coupons.destcountry, 
        coupons.deststatefips,
        coupons.deststate,
        coupons.deststatename,
        coupons.destwac
    from
        q2_ticket_data as tickets,
        q2_coupon_data as coupons
    where
        tickets.itinid = coupons.itinid;
    ''',
    'table',
    table_name='tickets_with_destination',
)

tickets_with_destination = sql_solid(
    'tickets_with_destination',
    '''
    select
        tickets.*,
        coupons.dest,
        coupons.destairportid,
        coupons.destairportseqid, coupons.destcitymarketid,
        coupons.destcountry, 
        coupons.deststatefips,
        coupons.deststate,
        coupons.deststatename,
        coupons.destwac
    from
        q2_ticket_data as tickets,
        q2_coupon_data as coupons
    where
        tickets.itinid = coupons.itinid;
    ''',
    'table',
    table_name='tickets_with_destination',
)

delays_vs_fares = sql_solid(
    'delays_vs_fares',
    '''
    with avg_fares as (
        select
            tickets.origin,
            tickets.dest,
            avg(cast(tickets.itinfare as float)) as avg_fare,
            avg(cast(tickets.farepermile as float)) as avg_fare_per_mile
        from tickets_with_destination as tickets
        where origin = 'SFO'
        group by (tickets.origin, tickets.dest)
    )
    select
        avg_fares.*,
        avg(avg_delays.arrival_delay) as avg_arrival_delay,
        avg(avg_delays.departure_delay) as avg_departure_delay
    from
        avg_fares,
        average_sfo_outbound_avg_delays_by_destination as avg_delays
    where
        avg_fares.origin = avg_delays.origin and
        avg_fares.dest = avg_delays.destination
    group by (
        avg_fares.avg_fare,
        avg_fares.avg_fare_per_mile,
        avg_fares.origin,
        avg_delays.origin,
        avg_fares.dest,
        avg_delays.destination
    )
    ''',
    'table',
    table_name='delays_vs_fares',
    inputs=[
        InputDefinition('tickets_with_destination', SqlTableName),
        InputDefinition('average_sfo_outbound_avg_delays_by_destination', SqlTableName)
    ]
)

eastbound_delays = sql_solid(
    'eastbound_delays',
    '''
    select
        avg(cast(cast(arrdelay as float) as integer)) as avg_arrival_delay,
        avg(cast(cast(depdelay as float) as integer)) as avg_departure_delay,
        origin,
        dest as destination,
        count(1) as num_flights,
        avg(cast(dest_latitude as float)) as dest_latitude,
        avg(cast(dest_longitude as float)) as dest_longitude,
        avg(cast(origin_latitude as float)) as origin_latitude,
        avg(cast(origin_longitude as float)) as origin_longitude
    from q2_on_time_data
    where 
        cast(origin_longitude as float) < cast(dest_longitude as float) and
        originstate != 'HI' and
        deststate != 'HI' and
        originstate != 'AK' and
        deststate != 'AK'
    group by (origin,destination)
    order by num_flights desc
    limit 100;
    ''',
    'table',
    table_name='eastbound_delays'
)

westbound_delays = sql_solid(
    'westbound_delays',
    '''
    select
        avg(cast(cast(arrdelay as float) as integer)) as avg_arrival_delay,
        avg(cast(cast(depdelay as float) as integer)) as avg_departure_delay,
        origin,
        dest as destination,
        count(1) as num_flights,
        avg(cast(dest_latitude as float)) as dest_latitude,
        avg(cast(dest_longitude as float)) as dest_longitude,
        avg(cast(origin_latitude as float)) as origin_latitude,
        avg(cast(origin_longitude as float)) as origin_longitude
    from q2_on_time_data
    where
        cast(origin_longitude as float) > cast(dest_longitude as float) and
        originstate != 'HI' and
        deststate != 'HI' and
        originstate != 'AK' and
        deststate != 'AK'
    group by (origin,destination)
    order by num_flights desc
    limit 100;
    ''',
    'table',
    table_name='westbound_delays'
)

delays_by_geography = notebook_solid(
    'Delays by Geography.ipynb',
    inputs=[
        InputDefinition(
            'db_url',
            types.String,
            description='The db_url to use to construct a SQLAlchemy engine.',
        ),
        InputDefinition(
            'westbound_delays',
            SqlTableName,
            description='The SQL table containing westbound delays.',
        ),
        InputDefinition(
            'eastbound_delays',
            SqlTableName,
            description='The SQL table containing eastbound delays.',
        ),
    ],
    outputs=[
        OutputDefinition(
            dagster_type=types.Path,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        ),
    ],
)

delays_vs_fares_nb = notebook_solid(
    'Fares vs. Delays.ipynb',
    inputs=[
        InputDefinition(
            'db_url',
            types.String,
            description='The db_url to use to construct a SQLAlchemy engine.',
        ),
        InputDefinition(
            'table_name',
            SqlTableName,
            description='The SQL table to use for calcuations.',
        ),
    ],
    outputs=[
        OutputDefinition(
            dagster_type=types.Path,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        ),
    ],
)

sfo_delays_by_destination = notebook_solid(
    'SFO Delays by Destination.ipynb',
    inputs=[
        InputDefinition(
            'db_url',
            types.String,
            description='The db_url to use to construct a SQLAlchemy engine.',
        ),
        InputDefinition(
            'table_name',
            SqlTableName,
            description='The SQL table to use for calcuations.',
        ),
    ],
    outputs=[
        OutputDefinition(
            dagster_type=types.Path,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        ),
    ],
)
