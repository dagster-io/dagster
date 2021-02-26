"""A fully fleshed out demo dagster repository with many configurable options."""

import os
import re

import dagster_pyspark
from dagster import (
    AssetMaterialization,
    EventMetadataEntry,
    ExpectationResult,
    Field,
    FileHandle,
    InputDefinition,
    Int,
    Output,
    OutputDefinition,
    String,
    check,
    composite_solid,
    make_python_type_usable_as_dagster_type,
    solid,
)
from dagster.core.types.dagster_type import create_string_type
from dagster_aws.s3 import S3Coordinate
from dagstermill import define_dagstermill_solid
from pyspark.sql import DataFrame
from sqlalchemy import text

from .cache_file_from_s3 import cache_file_from_s3
from .unzip_file_handle import unzip_file_handle

SqlTableName = create_string_type("SqlTableName", description="The name of a database table")


# Make pyspark.sql.DataFrame map to dagster_pyspark.DataFrame
make_python_type_usable_as_dagster_type(
    python_type=DataFrame, dagster_type=dagster_pyspark.DataFrame
)


PARQUET_SPECIAL_CHARACTERS = r"[ ,;{}()\n\t=]"


def _notebook_path(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "notebooks", name)


# start_solids_marker_3
def notebook_solid(name, notebook_path, input_defs, output_defs, required_resource_keys):
    return define_dagstermill_solid(
        name,
        _notebook_path(notebook_path),
        input_defs,
        output_defs,
        required_resource_keys=required_resource_keys,
    )


# end_solids_marker_3


# need a sql context w a sqlalchemy engine
def sql_solid(name, select_statement, materialization_strategy, table_name=None, input_defs=None):
    """Return a new solid that executes and materializes a SQL select statement.

    Args:
        name (str): The name of the new solid.
        select_statement (str): The select statement to execute.
        materialization_strategy (str): Must be 'table', the only currently supported
            materialization strategy. If 'table', the kwarg `table_name` must also be passed.
    Kwargs:
        table_name (str): THe name of the new table to create, if the materialization strategy
            is 'table'. Default: None.
        input_defs (list[InputDefinition]): Inputs, if any, for the new solid. Default: None.

    Returns:
        function:
            The new SQL solid.
    """
    input_defs = check.opt_list_param(input_defs, "input_defs", InputDefinition)

    materialization_strategy_output_types = {  # pylint:disable=C0103
        "table": SqlTableName,
        # 'view': String,
        # 'query': SqlAlchemyQueryType,
        # 'subquery': SqlAlchemySubqueryType,
        # 'result_proxy': SqlAlchemyResultProxyType,
        # could also materialize as a Pandas table, as a Spark table, as an intermediate file, etc.
    }

    if materialization_strategy not in materialization_strategy_output_types:
        raise Exception(
            "Invalid materialization strategy {materialization_strategy}, must "
            "be one of {materialization_strategies}".format(
                materialization_strategy=materialization_strategy,
                materialization_strategies=str(list(materialization_strategy_output_types.keys())),
            )
        )

    if materialization_strategy == "table":
        if table_name is None:
            raise Exception("Missing table_name: required for materialization strategy 'table'")

    output_description = (
        "The string name of the new table created by the solid"
        if materialization_strategy == "table"
        else "The materialized SQL statement. If the materialization_strategy is "
        "'table', this is the string name of the new table created by the solid."
    )

    description = """This solid executes the following SQL statement:
    {select_statement}""".format(
        select_statement=select_statement
    )

    # n.b., we will eventually want to make this resources key configurable
    sql_statement = (
        "drop table if exists {table_name};\n" "create table {table_name} as {select_statement};"
    ).format(table_name=table_name, select_statement=select_statement)

    # start_solids_marker_1
    @solid(
        name=name,
        input_defs=input_defs,
        output_defs=[
            OutputDefinition(
                materialization_strategy_output_types[materialization_strategy],
                description=output_description,
            )
        ],
        description=description,
        required_resource_keys={"db_info"},
        tags={"kind": "sql", "sql": sql_statement},
    )
    def _sql_solid(context, **input_defs):  # pylint: disable=unused-argument
        """Inner function defining the new solid.

        Args:
            context (SolidExecutionContext): Must expose a `db` resource with an `execute` method,
                like a SQLAlchemy engine, that can execute raw SQL against a database.

        Returns:
            str:
                The table name of the newly materialized SQL select statement.
        """
        context.log.info(
            "Executing sql statement:\n{sql_statement}".format(sql_statement=sql_statement)
        )
        context.resources.db_info.engine.execute(text(sql_statement))
        yield Output(value=table_name, output_name="result")

    # end_solids_marker_1
    return _sql_solid


@solid(
    required_resource_keys={
        "pyspark_step_launcher",
        "pyspark",
        "file_manager",
    },
    description=(
        "Take a file handle that contains a csv with headers and load it"
        "into a Spark DataFrame. It infers header names but does *not* infer schema.\n\n"
        "It also ensures that the column names are valid parquet column names by "
        "filtering out any of the following characters from column names:\n\n"
        f"Characters (within quotations): {PARQUET_SPECIAL_CHARACTERS}"
    ),
    output_defs=[OutputDefinition(DataFrame, io_manager_key="pyspark_io_manager")],
)
def ingest_csv_file_handle_to_spark(context, csv_file_handle: FileHandle):
    # fs case: copies from file manager location into system temp
    #    - This is potentially an unnecessary copy. We could potentially specialize
    #    the implementation of copy_handle_to_local_temp to not to do this in the
    #    local fs case. Somewhat more dangerous though.
    # s3 case: downloads from s3 to local temp directory
    temp_file_name = context.resources.file_manager.copy_handle_to_local_temp(csv_file_handle)

    # In fact for a generic component this should really be using
    # the spark APIs to load directly from whatever object store, rather
    # than using any interleaving temp files.
    data_frame = (
        context.resources.pyspark.spark_session.read.format("csv")
        .options(
            header="true",
            # inferSchema='true',
        )
        .load(temp_file_name)
    )

    # parquet compat
    return rename_spark_dataframe_columns(
        data_frame, lambda x: re.sub(PARQUET_SPECIAL_CHARACTERS, "", x)
    )


def rename_spark_dataframe_columns(data_frame, fn):
    return data_frame.toDF(*[fn(c) for c in data_frame.columns])


def do_prefix_column_names(df, prefix):
    check.inst_param(df, "df", DataFrame)
    check.str_param(prefix, "prefix")
    return rename_spark_dataframe_columns(df, lambda c: "{prefix}{c}".format(prefix=prefix, c=c))


@solid(
    required_resource_keys={"pyspark_step_launcher"},
    input_defs=[InputDefinition(name="data_frame", dagster_type=DataFrame)],
    output_defs=[OutputDefinition(DataFrame, io_manager_key="pyspark_io_manager")],
)
def canonicalize_column_names(_context, data_frame):
    return rename_spark_dataframe_columns(data_frame, lambda c: c.lower())


def replace_values_spark(data_frame, old, new):
    return data_frame.na.replace(old, new)


@solid(
    required_resource_keys={"pyspark_step_launcher"},
    input_defs=[InputDefinition(name="sfo_weather_data", dagster_type=DataFrame)],
    output_defs=[OutputDefinition(DataFrame, io_manager_key="pyspark_io_manager")],
)
def process_sfo_weather_data(_context, sfo_weather_data):
    normalized_sfo_weather_data = replace_values_spark(sfo_weather_data, "M", None)
    return rename_spark_dataframe_columns(normalized_sfo_weather_data, lambda c: c.lower())


# start_solids_marker_0
@solid(
    input_defs=[InputDefinition(name="data_frame", dagster_type=DataFrame)],
    output_defs=[OutputDefinition(name="table_name", dagster_type=String)],
    config_schema={"table_name": String},
    required_resource_keys={"db_info", "pyspark_step_launcher"},
)
def load_data_to_database_from_spark(context, data_frame):
    context.resources.db_info.load_table(data_frame, context.solid_config["table_name"])

    table_name = context.solid_config["table_name"]
    yield AssetMaterialization(
        asset_key="table:{table_name}".format(table_name=table_name),
        description=(
            "Persisted table {table_name} in database configured in the db_info resource."
        ).format(table_name=table_name),
        metadata_entries=[
            EventMetadataEntry.text(label="Host", text=context.resources.db_info.host),
            EventMetadataEntry.text(label="Db", text=context.resources.db_info.db_name),
        ],
    )
    yield Output(value=table_name, output_name="table_name")


# end_solids_marker_0


@solid(
    required_resource_keys={"pyspark_step_launcher"},
    description="Subsample a spark dataset via the configuration option.",
    config_schema={
        "subsample_pct": Field(
            Int,
            description="The integer percentage of rows to sample from the input dataset.",
        )
    },
    input_defs=[InputDefinition(name="data_frame", dagster_type=DataFrame)],
    output_defs=[OutputDefinition(DataFrame, io_manager_key="pyspark_io_manager")],
)
def subsample_spark_dataset(context, data_frame):
    return data_frame.sample(
        withReplacement=False, fraction=context.solid_config["subsample_pct"] / 100.0
    )


@composite_solid(
    description=(
        "Ingest a zipped csv file from s3, stash in a keyed file store (does not download if "
        "already present by default), unzip that file, and load it into a Spark Dataframe. See "
        "documentation in constituent solids for more detail."
    ),
)
def s3_to_df(s3_coordinate: S3Coordinate, archive_member: String) -> DataFrame:
    return ingest_csv_file_handle_to_spark(
        unzip_file_handle(cache_file_from_s3(s3_coordinate), archive_member)
    )


@composite_solid(
    config_fn=lambda cfg: {
        "subsample_spark_dataset": {"config": {"subsample_pct": cfg["subsample_pct"]}},
        "load_data_to_database_from_spark": {"config": {"table_name": cfg["table_name"]}},
    },
    config_schema={"subsample_pct": int, "table_name": str},
    description=(
        "Ingest zipped csv file from s3, load into a Spark DataFrame, optionally subsample it "
        "(via configuring the subsample_spark_dataset, solid), canonicalize the column names, "
        "and then load it into a data warehouse."
    ),
)
def s3_to_dw_table(s3_coordinate: S3Coordinate, archive_member: String) -> String:
    return load_data_to_database_from_spark(
        canonicalize_column_names(subsample_spark_dataset(s3_to_df(s3_coordinate, archive_member)))
    )


q2_sfo_outbound_flights = sql_solid(
    "q2_sfo_outbound_flights",
    """
    select * from q2_on_time_data
    where origin = 'SFO'
    """,
    "table",
    table_name="q2_sfo_outbound_flights",
)

average_sfo_outbound_avg_delays_by_destination = sql_solid(
    "average_sfo_outbound_avg_delays_by_destination",
    """
    select
        cast(cast(arrdelay as float) as integer) as arrival_delay,
        cast(cast(depdelay as float) as integer) as departure_delay,
        origin,
        dest as destination
    from q2_sfo_outbound_flights
    """,
    "table",
    table_name="average_sfo_outbound_avg_delays_by_destination",
    input_defs=[InputDefinition("q2_sfo_outbound_flights", dagster_type=SqlTableName)],
)

ticket_prices_with_average_delays = sql_solid(
    "tickets_with_destination",
    """
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
    """,
    "table",
    table_name="tickets_with_destination",
)

tickets_with_destination = sql_solid(
    "tickets_with_destination",
    """
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
    """,
    "table",
    table_name="tickets_with_destination",
)

delays_vs_fares = sql_solid(
    "delays_vs_fares",
    """
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
    """,
    "table",
    table_name="delays_vs_fares",
    input_defs=[
        InputDefinition("tickets_with_destination", SqlTableName),
        InputDefinition("average_sfo_outbound_avg_delays_by_destination", SqlTableName),
    ],
)

eastbound_delays = sql_solid(
    "eastbound_delays",
    """
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
    """,
    "table",
    table_name="eastbound_delays",
)

# start_solids_marker_2
westbound_delays = sql_solid(
    "westbound_delays",
    """
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
    """,
    "table",
    table_name="westbound_delays",
)
# end_solids_marker_2

# start_solids_marker_4
delays_by_geography = notebook_solid(
    "delays_by_geography",
    "Delays_by_Geography.ipynb",
    input_defs=[
        InputDefinition(
            "westbound_delays",
            SqlTableName,
            description="The SQL table containing westbound delays.",
        ),
        InputDefinition(
            "eastbound_delays",
            SqlTableName,
            description="The SQL table containing eastbound delays.",
        ),
    ],
    output_defs=[
        OutputDefinition(
            dagster_type=FileHandle,
            # name='plots_pdf_path',
            description="The saved PDF plots.",
        )
    ],
    required_resource_keys={"db_info"},
)
# end_solids_marker_4

delays_vs_fares_nb = notebook_solid(
    "fares_vs_delays",
    "Fares_vs_Delays.ipynb",
    input_defs=[
        InputDefinition(
            "table_name", SqlTableName, description="The SQL table to use for calcuations."
        )
    ],
    output_defs=[
        OutputDefinition(
            dagster_type=FileHandle,
            # name='plots_pdf_path',
            description="The path to the saved PDF plots.",
        )
    ],
    required_resource_keys={"db_info"},
)

sfo_delays_by_destination = notebook_solid(
    "sfo_delays_by_destination",
    "SFO_Delays_by_Destination.ipynb",
    input_defs=[
        InputDefinition(
            "table_name", SqlTableName, description="The SQL table to use for calcuations."
        )
    ],
    output_defs=[
        OutputDefinition(
            dagster_type=FileHandle,
            # name='plots_pdf_path',
            description="The path to the saved PDF plots.",
        )
    ],
    required_resource_keys={"db_info"},
)


@solid(
    required_resource_keys={"pyspark_step_launcher", "pyspark"},
    config_schema={"subsample_pct": Int},
    description=(
        "This solid takes April, May, and June data and coalesces it into a Q2 data set. "
        "It then joins the that origin and destination airport with the data in the "
        "master_cord_data."
    ),
    input_defs=[
        InputDefinition(name="april_data", dagster_type=DataFrame),
        InputDefinition(name="may_data", dagster_type=DataFrame),
        InputDefinition(name="june_data", dagster_type=DataFrame),
        InputDefinition(name="master_cord_data", dagster_type=DataFrame),
    ],
    output_defs=[OutputDefinition(DataFrame, io_manager_key="pyspark_io_manager")],
)
def join_q2_data(
    context,
    april_data,
    may_data,
    june_data,
    master_cord_data,
):

    dfs = {"april": april_data, "may": may_data, "june": june_data}

    missing_things = []

    for required_column in ["DestAirportSeqID", "OriginAirportSeqID"]:
        for month, df in dfs.items():
            if required_column not in df.columns:
                missing_things.append({"month": month, "missing_column": required_column})

    yield ExpectationResult(
        success=not bool(missing_things),
        label="airport_ids_present",
        description="Sequence IDs present in incoming monthly flight data.",
        metadata_entries=[
            EventMetadataEntry.json(label="metadata", data={"missing_columns": missing_things})
        ],
    )

    yield ExpectationResult(
        success=set(april_data.columns) == set(may_data.columns) == set(june_data.columns),
        label="flight_data_same_shape",
        metadata_entries=[
            EventMetadataEntry.json(label="metadata", data={"columns": april_data.columns})
        ],
    )

    q2_data = april_data.union(may_data).union(june_data)
    sampled_q2_data = q2_data.sample(
        withReplacement=False, fraction=context.solid_config["subsample_pct"] / 100.0
    )
    sampled_q2_data.createOrReplaceTempView("q2_data")

    dest_prefixed_master_cord_data = do_prefix_column_names(master_cord_data, "DEST_")
    dest_prefixed_master_cord_data.createOrReplaceTempView("dest_cord_data")

    origin_prefixed_master_cord_data = do_prefix_column_names(master_cord_data, "ORIGIN_")
    origin_prefixed_master_cord_data.createOrReplaceTempView("origin_cord_data")

    full_data = context.resources.pyspark.spark_session.sql(
        """
        SELECT * FROM origin_cord_data
        LEFT JOIN (
            SELECT * FROM q2_data
            LEFT JOIN dest_cord_data ON
            q2_data.DestAirportSeqID = dest_cord_data.DEST_AIRPORT_SEQ_ID
        ) q2_dest_data
        ON origin_cord_data.ORIGIN_AIRPORT_SEQ_ID = q2_dest_data.OriginAirportSeqID
        """
    )

    yield Output(rename_spark_dataframe_columns(full_data, lambda c: c.lower()))
