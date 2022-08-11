import os

from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import col, concat, lit
from pyspark.sql.functions import max as pyspark_max

from dagster import Field, In, String, graph, op, resource


def create_spark_session():
    return SparkSession.builder.getOrCreate()


def df_from_csv(path):
    spark_session = create_spark_session()
    return spark_session.read.option("header", True).format("csv").load(path)


def df_to_csv(df, path):
    df.toPandas().to_csv(path)


@resource(config_schema={"dir": Field(String)})
def source_data_dir(context):
    return context.resource_config["dir"]


@resource(config_schema={"dir": Field(String)})
def savedir(context):
    return context.resource_config["dir"]


@op(
    config_schema={
        "temperature_file": Field(String),
        "version_salt": Field(String),
    },
    required_resource_keys={"source_data_dir", "savedir"},
)
def get_max_temp_per_station(context):
    fpath = os.path.join(context.resources.source_data_dir, context.op_config["temperature_file"])
    tmpf_df = df_from_csv(fpath)
    w = Window.partitionBy("station")
    max_df = (
        tmpf_df.withColumn("maxTmpf", pyspark_max("tmpf").over(w))
        .where(col("tmpf") == col("maxTmpf"))
        .drop("maxTmpf")
    )
    selected_cols_df = max_df.selectExpr(
        ["station as airport_code", "valid as date", "tmpf as temperature_f"]
    )
    outpath = os.path.join(context.resources.savedir, "maxtemp.csv")
    df_to_csv(selected_cols_df, outpath)
    return outpath


@op(
    config_schema={"station_file": Field(String), "version_salt": Field(String)},
    required_resource_keys={"source_data_dir", "savedir"},
)
def get_consolidated_location(context):
    fpath = os.path.join(context.resources.source_data_dir, context.op_config["station_file"])
    station_df = df_from_csv(fpath)
    consolidated_df = station_df.withColumn(
        "full_address",
        concat(
            lit("Country: "),
            col("country"),
            lit(", State: "),
            col("state"),
            lit(", Zip: "),
            col("zip"),
        ),
    )
    consolidated_df = consolidated_df.select(col("station"), col("full_address"))
    outpath = os.path.join(context.resources.savedir, "stationcons.csv")
    df_to_csv(consolidated_df, outpath)
    return outpath


@op(
    config_schema={"version_salt": Field(String)},
    ins={"maxtemp_path": In(str), "stationcons_path": In(str)},
    required_resource_keys={"savedir"},
)
def combine_dfs(context, maxtemp_path, stationcons_path):
    maxtemps = df_from_csv(maxtemp_path)
    stationcons = df_from_csv(stationcons_path)
    joined_temps = maxtemps.join(stationcons, col("airport_code") == col("station")).select(
        col("full_address"), col("temperature_f")
    )
    outpath = os.path.join(context.resources.savedir, "temp_for_place.csv")
    df_to_csv(joined_temps, outpath)
    return outpath


@op(
    config_schema={"version_salt": Field(String)},
    ins={"path": In(str)},
    required_resource_keys={"savedir"},
)
def pretty_output(context, path):
    temp_for_place = df_from_csv(path)
    pretty_result = temp_for_place.withColumn(
        "temperature_info",
        concat(col("full_address"), lit(", temp (Fahrenheit): "), col("temperature_f")),
    )
    pretty_result = pretty_result.select(col("temperature_info"))
    outpath = os.path.join(context.resources.savedir, "pretty_output.csv")
    df_to_csv(pretty_result, outpath)
    return outpath


@graph
def pyspark_assets():
    pretty_output(combine_dfs(get_max_temp_per_station(), get_consolidated_location()))


dir_resources = {"source_data_dir": source_data_dir, "savedir": savedir}
pyspark_assets_job = pyspark_assets.to_job(resource_defs=dir_resources)

if __name__ == "__main__":
    run_config = {
        "ops": {
            "get_max_temp_per_station": {
                "config": {
                    "temperature_file": "temperature.csv",
                    "version_salt": "foo",
                }
            },
            "get_consolidated_location": {
                "config": {
                    "station_file": "stations.csv",
                    "version_salt": "foo",
                }
            },
            "combine_dfs": {
                "config": {
                    "version_salt": "foo",
                }
            },
            "pretty_output": {
                "config": {
                    "version_salt": "foo",
                }
            },
        },
        "resources": {
            "source_data_dir": {"config": {"dir": "asset_job_files"}},
            "savedir": {"config": {"dir": "asset_job_files"}},
        },
    }

    pyspark_assets_config_job = pyspark_assets.to_job(
        resource_defs={"source_data_dir": source_data_dir, "savedir": savedir}, config=run_config
    )

    result = pyspark_assets_config_job.execute_in_process()
