'''A fully fleshed out demo dagster repository with many configurable options.'''

import os
import shutil
import tempfile
import zipfile

from sqlalchemy import text

from dagster import (
    Any,
    Bool,
    Dict,
    Field,
    InputDefinition,
    Int,
    List,
    OutputDefinition,
    Path,
    Result,
    SolidDefinition,
    String,
    check,
    solid,
)
from dagstermill import define_dagstermill_solid

from .types import SparkDataFrameType, SqlTableName
from .utils import mkdir_p, S3Logger


def _notebook_path(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notebooks', name)


def notebook_solid(name, notebook_path, inputs, outputs):
    return define_dagstermill_solid(name, _notebook_path(notebook_path), inputs, outputs)


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
    inputs = check.opt_list_param(inputs, 'inputs', InputDefinition)

    materialization_strategy_output_types = {  # pylint:disable=C0103
        'table': SqlTableName,
        # 'view': String,
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
                materialization_strategies=str(list(materialization_strategy_output_types.keys())),
            )
        )

    if materialization_strategy == 'table':
        if table_name is None:
            raise Exception('Missing table_name: required for materialization strategy \'table\'')

    output_description = (
        'The string name of the new table created by the solid'
        if materialization_strategy == 'table'
        else 'The materialized SQL statement. If the materialization_strategy is '
        '\'table\', this is the string name of the new table created by the solid.'
    )

    description = '''This solid executes the following SQL statement:
    {select_statement}'''.format(
        select_statement=select_statement
    )

    # n.b., we will eventually want to make this resources key configurable
    sql_statement = (
        'drop table if exists {table_name};\n' 'create table {table_name} as {select_statement};'
    ).format(table_name=table_name, select_statement=select_statement)

    def transform_fn(context, _inputs):
        '''Inner function defining the new solid.

        Args:
            context (TransformExecutionContext): Must expose a `db` resource with an `execute`
                method, like a SQLAlchemy engine, that can execute raw SQL against a database.

        Returns:
            str:
                The table name of the newly materialized SQL select statement.
        '''

        context.log.info(
            'Executing sql statement:\n{sql_statement}'.format(sql_statement=sql_statement)
        )
        context.resources.db_info.engine.execute(text(sql_statement))
        yield Result(value=table_name, output_name='result')

    return SolidDefinition(
        name=name,
        inputs=inputs,
        outputs=[
            OutputDefinition(
                materialization_strategy_output_types[materialization_strategy],
                description=output_description,
            )
        ],
        transform_fn=transform_fn,
        description=description,
        metadata={'kind': 'sql', 'sql': sql_statement},
    )


@solid(
    name='download_from_s3',
    config_field=Field(
        List(
            Dict(
                fields={
                    # Probably want to make the region configuable too
                    'bucket': Field(
                        String, description='The S3 bucket in which to look for the key.'
                    ),
                    'key': Field(String, description='The key to download.'),
                    'skip_if_present': Field(
                        Bool,
                        description=(
                            'If True, and a file already exists at the path described by the '
                            'target_path config value, if present, or the key, then the solid '
                            'will no-op.'
                        ),
                        default_value=False,
                        is_optional=True,
                    ),
                    'target_path': Field(
                        Path,
                        description=(
                            'If present, specifies the path at which to download the object.'
                        ),
                        is_optional=True,
                    ),
                }
            )
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(List(Path), description='The path to the downloaded object.')],
)
def download_from_s3(context):
    '''Download an object from s3.

    Args:
        info (ExpectationExecutionInfo): Must expose a boto3 S3 client as its `s3` resource.

    Returns:
        str:
            The path to the downloaded object.
    '''
    filesystem = context.resources.filesystem

    results = []
    for file_ in context.solid_config:
        bucket = file_['bucket']
        key = file_['key']
        target_path = file_.get('target_path') or key

        if target_path is None:
            target_path = context.resources.tempfile.tempfile().name

        if file_['skip_if_present'] and filesystem.is_file(target_path):
            context.log.info(
                'Skipping download, file already present at {target_path}'.format(
                    target_path=target_path
                )
            )
        else:
            if os.path.dirname(target_path):
                mkdir_p(os.path.dirname(target_path))  # Need a decent filesystem solution to this

            context.log.info(
                'Starting download of {bucket}/{key} to {target_path}'.format(
                    bucket=bucket, key=key, target_path=target_path
                )
            )

            headers = context.resources.s3.head_object(Bucket=bucket, Key=key)
            logger = S3Logger(
                context.log.debug, bucket, key, target_path, int(headers['ContentLength'])
            )
            with filesystem.write(target_path) as file_obj:
                context.resources.s3.download_fileobj(
                    Bucket=bucket, Key=key, Fileobj=file_obj, Callback=logger
                )
        results.append(target_path)
    return results


@solid(
    name='upload_to_s3',
    config_field=Field(
        Dict(
            fields={
                # Probably want to make the region configuable too
                'bucket': Field(String, description='The S3 bucket to which to upload the file.'),
                'key': Field(String, description='The key to which to upload the file.'),
                'kwargs': Field(
                    Any,  # TODO fix
                    description='Kwargs to pass through to the S3 client',
                    is_optional=True,
                ),
            }
        )
    ),
    inputs=[InputDefinition('file_path', Path, description='The path of the file to upload.')],
    description='Uploads a file to S3.',
    outputs=[
        OutputDefinition(
            String, description='The bucket to which the file was uploaded.', name='bucket'
        ),
        OutputDefinition(String, description='The key to which the file was uploaded.', name='key'),
    ],
)
def upload_to_s3(context, file_path):
    '''Upload a file to s3.

    Args:
        info (ExpectationExecutionInfo): Must expose a boto3 S3 client as its `s3` resource.

    Returns:
        (str, str):
            The bucket and key to which the file was uploaded.
    '''
    bucket = context.solid_config['bucket']
    key = context.solid_config['key']

    with open(file_path, 'rb') as fd:
        context.resources.s3.put_object(
            Bucket=bucket, Body=fd, Key=key, **(context.solid_config.get('kwargs') or {})
        )
    yield Result(bucket, 'bucket')
    yield Result(key, 'key')


@solid(
    name='unzip_file',
    inputs=[
        InputDefinition('archive_paths', List(Path), description='The path to the archive.'),
        InputDefinition(
            'archive_members', List(String), description='The archive member to extract.'
        ),
    ],
    config_field=Field(
        Dict(
            fields={
                'skip_if_present': Field(
                    Bool,
                    description='If True, and a file already exists at the path to which the '
                    'archive member would be unzipped, then the solid will no-op',
                    default_value=False,
                    is_optional=True,
                ),
                'destination_dir': Field(
                    String,
                    description='If no destination_dir is specified, the archive will be unzipped '
                    'to a temporary directory.',
                    is_optional=True,
                ),
            }
        )
    ),
    description='Extracts an archive member from a zip archive.',
    outputs=[OutputDefinition(List(Path), description='The path to the unzipped archive member.')],
)
def unzip_file(context, archive_paths, archive_members):
    def extract(context, archive_path, zip_ref, archive_member, destination_dir, skip_if_present):
        filesystem = context.resources.filesystem

        target_path = filesystem.join(destination_dir, archive_member)
        is_file = filesystem.is_file(target_path)
        is_dir = filesystem.is_dir(target_path)

        if not (skip_if_present and (is_file or is_dir)):
            tempdir = tempfile.mkdtemp()
            try:
                extracted_path = zip_ref.extract(archive_member, tempdir)
                with filesystem.write(
                    filesystem.join(destination_dir, os.path.basename(extracted_path))
                ) as write_obj:
                    with open(extracted_path, 'rb') as read_obj:
                        write_obj.write(read_obj.read())
            finally:
                shutil.rmtree(tempdir)
        else:
            if is_file:
                context.log.info(
                    'Skipping unarchive of {archive_member} from {archive_path}, '
                    'file already present at {target_path}'.format(
                        archive_member=archive_member,
                        archive_path=archive_path,
                        target_path=target_path,
                    )
                )
            if is_dir:
                context.log.info(
                    'Skipping unarchive of {archive_member} from {archive_path}, '
                    'directory already present at {target_path}'.format(
                        archive_member=archive_member,
                        archive_path=archive_path,
                        target_path=target_path,
                    )
                )

        return target_path

    filesystem = context.resources.filesystem
    skip_if_present = context.solid_config['skip_if_present']

    results = []
    for (i, archive_path) in enumerate(archive_paths):
        destination_dir = os.path.dirname(archive_path)
        if archive_members:
            archive_member = archive_members[i]
        else:
            archive_member = None

        with filesystem.read(archive_path) as file_obj:
            with zipfile.ZipFile(file_obj, 'r') as zip_ref:
                if archive_member is not None:
                    target_path = extract(
                        context,
                        archive_path,
                        zip_ref,
                        archive_member,
                        destination_dir,
                        skip_if_present,
                    )
                    results.append(target_path)
                else:
                    for archive_member in zip_ref.namelist():
                        target_path = extract(
                            context,
                            archive_path,
                            zip_ref,
                            archive_member,
                            destination_dir,
                            skip_if_present,
                        )
                        results.append(target_path)
    return results


@solid(
    name='ingest_csv_to_spark',
    inputs=[InputDefinition('input_csv', Path)],
    outputs=[OutputDefinition(SparkDataFrameType)],
)
def ingest_csv_to_spark(context, input_csv):
    target_path = context.resources.tempfile.tempfile().name
    with context.resources.filesystem.read(input_csv) as read_obj:
        with open(target_path, 'wb') as write_obj:
            write_obj.write(read_obj.read())

    data_frame = (
        context.resources.spark.read.format('csv')
        .options(
            header='true',
            # inferSchema='true',
        )
        .load(target_path)
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
            description='The data frame whose columns should be prefixed',
        )
    ],
    config_field=Field(String, description='Prefix to append.'),
    outputs=[OutputDefinition(SparkDataFrameType)],
)
def prefix_column_names(context, data_frame):
    return rename_spark_dataframe_columns(
        data_frame, lambda c: '{prefix}{c}'.format(prefix=context.solid_config, c=c)
    )


@solid(
    name='canonicalize_column_names',
    inputs=[
        InputDefinition(
            'data_frame', SparkDataFrameType, description='The data frame to canonicalize'
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
)
def canonicalize_column_names(_context, data_frame):
    return rename_spark_dataframe_columns(data_frame, lambda c: c.lower())


def replace_values_spark(data_frame, old, new):
    return data_frame.na.replace(old, new)


@solid(
    name='normalize_weather_na_values',
    description="Normalizes the given NA values by replacing them with None",
    # FIXME can this be optional
    # config_field=Field(
    #     String,
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
def normalize_weather_na_values(_context, data_frame):
    return replace_values_spark(data_frame, 'M', None)


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
    config_field=Field(Dict(fields={'table_name': Field(String, description='')})),
)
def load_data_to_database_from_spark(context, data_frame):
    context.resources.db_info.load_table(data_frame, context.solid_config['table_name'])
    return data_frame


@solid(
    name='subsample_spark_dataset',
    description='Subsample a spark dataset.',
    config_field=Field(
        Dict(fields={'subsample_pct': Field(Int, description='')})
        # description='The integer percentage of rows to sample from the input dataset.'
    ),
    inputs=[
        InputDefinition(
            'data_frame', SparkDataFrameType, description='The pyspark DataFrame to subsample.'
        )
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            # description='A pyspark DataFrame containing a subsample of the input rows.',
        )
    ],
)
def subsample_spark_dataset(context, data_frame):
    return data_frame.sample(False, context.solid_config['subsample_pct'] / 100.0)


@solid(
    name='join_spark_data_frames',
    inputs=[
        InputDefinition(
            'left_data_frame', SparkDataFrameType, description='The left DataFrame to join.'
        ),
        InputDefinition(
            'right_data_frame', SparkDataFrameType, description='The right DataFrame to join.'
        ),
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            # description='A pyspark DataFrame containing a subsample of the input rows.',
        )
    ],
    config_field=Field(
        Dict(
            fields={
                'on_left': Field(String, description='', default_value='id', is_optional=True),
                'on_right': Field(String, description='', default_value='id', is_optional=True),
                'how': Field(String, description='', default_value='inner', is_optional=True),
            }
        )
    ),
)
def join_spark_data_frames(context, left_data_frame, right_data_frame):
    return left_data_frame.join(
        right_data_frame,
        on=(
            getattr(left_data_frame, context.solid_config['on_left'])
            == getattr(right_data_frame, context.solid_config['on_right'])
        ),
        how=context.solid_config['how'],
    )


@solid(
    name='union_spark_data_frames',
    inputs=[
        InputDefinition(
            'left_data_frame', SparkDataFrameType, description='The left DataFrame to union.'
        ),
        InputDefinition(
            'right_data_frame', SparkDataFrameType, description='The right DataFrame to union.'
        ),
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            description='A pyspark DataFrame containing the union of the input data frames.',
        )
    ],
)
def union_spark_data_frames(_context, left_data_frame, right_data_frame):
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
    inputs=[InputDefinition('q2_sfo_outbound_flights', dagster_type=SqlTableName)],
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
        InputDefinition('average_sfo_outbound_avg_delays_by_destination', SqlTableName),
    ],
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
    table_name='eastbound_delays',
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
    table_name='westbound_delays',
)

delays_by_geography = notebook_solid(
    'delays_by_geography',
    'Delays_by_Geography.ipynb',
    inputs=[
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
            dagster_type=Path,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        )
    ],
)

delays_vs_fares_nb = notebook_solid(
    'fares_vs_delays',
    'Fares_vs_Delays.ipynb',
    inputs=[
        InputDefinition(
            'table_name', SqlTableName, description='The SQL table to use for calcuations.'
        )
    ],
    outputs=[
        OutputDefinition(
            dagster_type=Path,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        )
    ],
)

sfo_delays_by_destination = notebook_solid(
    'sfo_delays_by_destination',
    'SFO_Delays_by_Destination.ipynb',
    inputs=[
        InputDefinition(
            'table_name', SqlTableName, description='The SQL table to use for calcuations.'
        )
    ],
    outputs=[
        OutputDefinition(
            dagster_type=Path,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        )
    ],
)
