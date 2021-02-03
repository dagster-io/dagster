import json
import os
import pickle
import tempfile
import uuid
from datetime import timedelta
from time import gmtime, strftime
from typing import Tuple
from zipfile import ZipFile

import requests
from dagster import (
    Any,
    AssetMaterialization,
    DagsterType,
    EventMetadataEntry,
    Field,
    InputDefinition,
    Output,
    OutputDefinition,
    check,
    composite_solid,
    solid,
)
from dagster.utils import PICKLE_PROTOCOL
from dagster_examples.bay_bikes.constants import (
    DARK_SKY_BASE_URL,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    WEATHER_COLUMNS,
)
from dagster_examples.bay_bikes.types import (
    RawTripDataFrame,
    TrafficDataFrame,
    TrainingSet,
    TripDataFrame,
    WeatherDataFrame,
)
from dagster_pandas import DataFrame as DagsterPandasDataFrame
from keras.layers import LSTM, Dense
from keras.models import Sequential
from numpy import array, ndarray, transpose
from pandas import (
    DataFrame,
    date_range,
    get_dummies,
    json_normalize,
    notnull,
    read_csv,
    read_sql_table,
    to_datetime,
)

# Added this to silence tensorflow logs. They are insanely verbose.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def _write_chunks_to_fp(response, output_fp, chunk_size):
    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            output_fp.write(chunk)


def _download_zipfile_from_url(url: str, target: str, chunk_size=8192) -> str:
    with requests.get(url, stream=True) as response, open(target, "wb+") as output_fp:
        response.raise_for_status()
        _write_chunks_to_fp(response, output_fp, chunk_size)
    return target


@solid(
    input_defs=[InputDefinition("file_name", str), InputDefinition("base_url", str)],
    output_defs=[OutputDefinition(str)],
    config_schema={"chunk_size": Field(int, is_required=False, default_value=8192)},
    required_resource_keys={"volume"},
)
def download_zipfile_from_url(context, file_name: str, base_url: str):
    url = "/".join([base_url, file_name])
    # mount dirs onto volume
    target = os.path.join(context.resources.volume, file_name)
    if not os.path.exists(target):
        _download_zipfile_from_url(
            url,
            target,
            context.solid_config["chunk_size"],
        )
    yield AssetMaterialization(
        asset_key=file_name,
        metadata_entries=[
            EventMetadataEntry.text(url, "zipfile url source"),
            EventMetadataEntry.text(target, "zipfile filepath"),
            EventMetadataEntry.text(str(os.path.getsize(target)), "size of zipfile (bytes)"),
        ],
    )
    yield Output(target)


@solid(
    input_defs=[
        InputDefinition("input_file_path", str),
        InputDefinition("target_csv_file_in_archive", str),
    ],
    output_defs=[OutputDefinition(DagsterPandasDataFrame)],
    config_schema={
        "delimiter": Field(
            str,
            default_value=",",
            is_required=False,
            description=("A one-character string used to separate fields."),
        ),
        "compression": Field(
            str,
            default_value="infer",
            is_required=False,
        ),
    },
    required_resource_keys={"volume"},
)
def load_compressed_csv_file(
    context, input_file_path: str, target_csv_file_in_archive: str
) -> DataFrame:
    # There must be a header in all of these dataframes or it becomes had to load into a table or concat dataframes.
    dataset = read_csv(
        ZipFile(input_file_path).open(target_csv_file_in_archive),
        sep=context.solid_config["delimiter"],
        header=0,
        index_col=0,
        compression=context.solid_config["compression"],
    )
    return dataset


@solid(required_resource_keys={"gcs_client"})
def upload_pickled_object_to_gcs_bucket(context, value: Any, bucket_name: str, file_name: str):
    gcs_bucket = context.resources.gcs_client.get_bucket(bucket_name)
    key = "{}-{}".format(file_name, uuid.uuid4())
    with tempfile.TemporaryFile("w+b") as fp:
        pickle.dump(value, fp, PICKLE_PROTOCOL)
        # Done because you can't upload the contents of a file outside the context manager if it's a tempfile.
        fp.seek(0)
        gcs_bucket.blob(key).upload_from_file(fp)

    gcs_url = "gs://{bucket_name}/{key}".format(bucket_name=bucket_name, key=key)

    yield AssetMaterialization(
        asset_key=gcs_url,
        description="Serialized object to Google Cloud Storage Bucket",
        metadata_entries=[
            EventMetadataEntry.text(gcs_url, "google cloud storage URI"),
        ],
    )
    yield Output(value)


def _create_and_load_staging_table(engine, table_name, records):
    create_table_sql = "create table if not exists {table_name} (id serial not null primary key, staging_data json not null);".format(
        table_name=table_name
    )
    engine.execute(create_table_sql)
    records = records.where(notnull(records), None)
    insert_sql = "insert into {table_name} (staging_data) values {data};".format(
        table_name=table_name,
        data=",".join(
            [
                "('{record}')".format(record=json.dumps(record).replace("'", ""))
                for record in records.to_dict("records")
            ]
        ),
    )
    engine.execute(insert_sql)


@solid(
    input_defs=[
        InputDefinition("records", DagsterPandasDataFrame),
        InputDefinition("table_name", str),
    ],
    output_defs=[OutputDefinition(str, name="staging_table")],
    required_resource_keys={"postgres_db"},
)
def insert_into_staging_table(context, records: DataFrame, table_name: str):
    _create_and_load_staging_table(context.resources.postgres_db.engine, table_name, records)
    yield AssetMaterialization(
        asset_key=table_name,
        description="Table {} created in database {}".format(
            table_name, context.resources.postgres_db.db_name
        ),
        metadata_entries=[EventMetadataEntry.text(str(len(records)), "num rows inserted")],
    )
    yield Output(output_name="staging_table", value=table_name)


def create_download_table_as_dataframe_solid(name, expected_dagster_pandas_dataframe_type):
    check.str_param(name, "name")
    check.inst_param(
        expected_dagster_pandas_dataframe_type,
        "expected_dagster_pandas_dataframe_schema",
        DagsterType,
    )

    @solid(
        input_defs=[InputDefinition("table_name", str)],
        output_defs=[OutputDefinition(expected_dagster_pandas_dataframe_type)],
        config_schema={"subsets": Field([str], is_required=False)},
        required_resource_keys={"postgres_db"},
        name=name,
    )
    def download_table_as_dataframe(context, table_name: str) -> DataFrame:
        dataframe = read_sql_table(
            table_name,
            context.resources.postgres_db.engine,
        )
        # flatten dataframe
        dataframe = json_normalize(dataframe.to_dict("records"))
        dataframe.columns = [column.split(".")[-1] for column in dataframe.columns]
        # De-Duplicate Table
        subsets = context.solid_config.get("subsets", None)
        return dataframe.drop_duplicates(subset=subsets if subsets else None)

    return download_table_as_dataframe


@solid(
    input_defs=[InputDefinition("epoch_date", int)],
    output_defs=[OutputDefinition(DagsterPandasDataFrame)],
    config_schema={
        "latitude": Field(
            float,
            default_value=37.8267,
            is_required=False,
            description=("Latitude coordinate to get weather data about. Default is SF."),
        ),
        "longitude": Field(
            float,
            default_value=-122.4233,
            is_required=False,
            description=("Longitude coordinate to get weather data about. Default is SF."),
        ),
        "times_to_exclude": Field(
            [str],
            default_value=["currently", "minutely", "hourly", "alerts", "flags"],
            is_required=False,
            description="data granularities to exclude when making this api call",
        ),
    },
    required_resource_keys={"credentials_vault"},
)
def download_weather_report_from_weather_api(context, epoch_date: int) -> DataFrame:
    # Make API Call
    coordinates = "{0},{1}".format(
        context.solid_config["latitude"], context.solid_config["longitude"]
    )
    weather_api_key = context.resources.credentials_vault.credentials["DARK_SKY_API_KEY"]
    url_prefix = "/".join([DARK_SKY_BASE_URL, weather_api_key, coordinates])
    url = url_prefix + ",{}?exclude={}".format(
        epoch_date, ",".join(context.solid_config["times_to_exclude"])
    )
    context.log.info("Sending Request. URL is: {}".format(url))
    response = requests.get(url)
    response.raise_for_status()
    raw_weather_data = response.json()["daily"]["data"][0]
    return DataFrame([raw_weather_data])


@solid(
    input_defs=[InputDefinition(name="dataframe", dagster_type=RawTripDataFrame)],
    output_defs=[OutputDefinition(name="trip_dataframe", dagster_type=TripDataFrame)],
)
def preprocess_trip_dataset(_, dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe[["bike_id", "start_time", "end_time"]].dropna(how="all").reindex()
    dataframe["bike_id"] = dataframe["bike_id"].astype("int64")
    dataframe["start_time"] = to_datetime(dataframe["start_time"])
    dataframe["end_time"] = to_datetime(dataframe["end_time"])
    dataframe["interval_date"] = dataframe["start_time"].apply(lambda x: x.date())
    yield Output(dataframe, output_name="trip_dataframe")


@solid(
    input_defs=[InputDefinition("dataframe", DagsterPandasDataFrame)],
    output_defs=[OutputDefinition(name="weather_dataframe", dagster_type=WeatherDataFrame)],
)
def preprocess_weather_dataset(_, dataframe: DataFrame) -> DataFrame:
    """
    Steps:

    1. Converts time columns to match the date types in the traffic dataset so
    that we can join effectively.

    2. Fills N/A values in ozone, so that we have the right datatypes.

    3. Convert precipType to a column that's more amenable to one hot encoding.
    """
    dataframe = dataframe[WEATHER_COLUMNS].dropna(how="all").reindex()
    # These are to address weird corner cases where columns are NA
    # This fill is because the weather API fails to have a summary for certain types of clear days.
    dataframe["summary"] = dataframe["summary"].fillna("Clear throughout the day.")
    dataframe["icon"] = dataframe["icon"].fillna("clear-day")
    # This happens frequently, I defaulted to the average.
    dataframe["temperatureLow"] = dataframe["temperatureLow"].fillna(
        dataframe.temperatureLow.mean()
    )
    # This happens frequently as well, I defaulted to the median since this is a time datatype
    dataframe["temperatureLowTime"] = (
        dataframe["temperatureLowTime"]
        .fillna(dataframe.temperatureLowTime.median())
        .astype("int64")
    )
    # This happens frequently, the median felt like the appropriate statistic. Can change this over time.
    dataframe["ozone"] = dataframe["ozone"].fillna(dataframe.ozone.median())
    dataframe["time"] = to_datetime(
        dataframe["time"].apply(lambda epoch_ts: strftime("%Y-%m-%d", gmtime(epoch_ts)))
    )
    yield Output(dataframe, output_name="weather_dataframe")


@solid(
    input_defs=[InputDefinition("trip_dataset", dagster_type=TripDataFrame)],
    output_defs=[OutputDefinition(name="traffic_dataframe", dagster_type=TrafficDataFrame)],
)
def transform_into_traffic_dataset(_, trip_dataset: DataFrame) -> DataFrame:
    def max_traffic_load(trips):
        interval_count = {
            start_interval: 0 for start_interval in date_range(trips.name, periods=24, freq="h")
        }
        for interval in interval_count.keys():
            upper_bound_interval = interval + timedelta(hours=1)
            # Count number of bikes in transit during sample interval
            interval_count[interval] = len(
                trips[
                    (
                        (  # Select trip if the trip started within the sample interval
                            (interval <= trips["start_time"])
                            & (trips["start_time"] < upper_bound_interval)
                        )
                        | (  # Select trip if the trip ended within the sample interval
                            (interval <= trips["end_time"])
                            & (trips["end_time"] < upper_bound_interval)
                        )
                        | (  # Select trip if the trip started AND ended outside of the interval
                            (trips["start_time"] < interval)
                            & (trips["end_time"] >= upper_bound_interval)
                        )
                    )
                ]
            )
        return max(interval_count.values())

    counts = trip_dataset.groupby(["interval_date"]).apply(max_traffic_load)
    traffic_dataset = DataFrame(counts).reset_index()
    traffic_dataset.columns = ["interval_date", "peak_traffic_load"]
    yield Output(traffic_dataset, output_name="traffic_dataframe")


class Timeseries:
    def __init__(self, sequence):
        self.sequence = check.opt_list_param(sequence, "sequence", of_type=(int, float))

    def convert_to_snapshot_sequence(self, memory_length):
        """
        A snapshot sequence is a transformation of a sequence into a sequence of snapshots which are the past
        {memory_length} observations in the sequence. This looks like the following:

        f([1, 2, 3, 4, 5], 2) -> [[1,2,3], [2,3,4], [3,4,5]]
        """
        if not self.sequence:
            raise ValueError("Cannot produce snapshots for an empty sequence")
        if memory_length < 1:
            raise ValueError("Invalid snapshot length.")
        if memory_length >= len(self.sequence):
            raise ValueError(
                "Unable to produce snapshots. Memory length is too large ({}) and the sequence is too small ({})".format(
                    memory_length, len(self.sequence)
                )
            )
        snapshot_sequence = []
        for index in range(len(self.sequence)):
            if index >= memory_length:
                snapshot = [
                    self.sequence[index - snapshot_delta]
                    for snapshot_delta in range(memory_length + 1)
                ]
                snapshot_sequence.append(snapshot[::-1])
        return snapshot_sequence


class MultivariateTimeseries:
    def __init__(
        self,
        input_sequences,
        output_sequence,
        input_sequence_names,
        output_sequence_name,
        elem_type=(int, float),
    ):
        self.input_timeseries_collection = [
            Timeseries(input_sequence)
            for input_sequence in check.matrix_param(
                input_sequences, "input_sequences", of_type=elem_type
            )
        ]
        self.output_timeseries = Timeseries(check.list_param(output_sequence, "output_sequence"))
        if len(input_sequence_names) != len(self.input_timeseries_collection):
            raise ValueError("Every timeseries needs a name attached to it.")
        self.input_timeseries_names = check.list_param(
            input_sequence_names, "input_sequence_names", of_type=str
        )
        self.output_timeseries_name = check.str_param(output_sequence_name, "output_sequence_name")

    def convert_to_snapshot_matrix(self, memory_length):
        # Transpose the matrix so that inputs match up with tensorflow tensor expectation
        input_snapshot_matrix = transpose(
            [
                timeseries.convert_to_snapshot_sequence(memory_length)
                for timeseries in self.input_timeseries_collection
            ],
            (1, 2, 0),
        )
        output_snapshot_sequence = self.output_timeseries.sequence[memory_length:]
        return array(input_snapshot_matrix), array(output_snapshot_sequence)

    @classmethod
    def from_dataframe(cls, dataframe, input_sequence_names, output_sequence_name):
        return cls(
            input_sequences=[
                dataframe[input_sequence_name].tolist()
                for input_sequence_name in input_sequence_names
            ],
            output_sequence=dataframe[output_sequence_name].tolist(),
            input_sequence_names=input_sequence_names,
            output_sequence_name=output_sequence_name,
        )


@solid(
    config_schema={"memory_length": Field(int, description="The window memory length")},
    input_defs=[
        InputDefinition("traffic_dataset", dagster_type=TrafficDataFrame),
        InputDefinition("weather_dataset", dagster_type=WeatherDataFrame),
    ],
    output_defs=[OutputDefinition(dagster_type=TrainingSet)],
)
def produce_training_set(
    context, traffic_dataset: DataFrame, weather_dataset: DataFrame
) -> Tuple[ndarray, ndarray]:
    traffic_dataset["time"] = to_datetime(traffic_dataset.interval_date)
    weather_dataset["time"] = to_datetime(weather_dataset.time)
    dataset = traffic_dataset.join(weather_dataset.set_index("time"), on="time")
    dataset = get_dummies(dataset, columns=["summary", "icon"])
    multivariate_timeseries = MultivariateTimeseries.from_dataframe(
        dataset, FEATURE_COLUMNS, LABEL_COLUMN
    )
    input_snapshot_matrix, output = multivariate_timeseries.convert_to_snapshot_matrix(
        context.solid_config["memory_length"]
    )
    return input_snapshot_matrix, output


@solid(
    config_schema={
        "timeseries_train_test_breakpoint": Field(
            int, description="The breakpoint between training and test set"
        ),
        "lstm_layer_config": {
            "activation": Field(str, is_required=False, default_value="relu"),
            "num_recurrant_units": Field(int, is_required=False, default_value=50),
        },
        "num_dense_layers": Field(int, is_required=False, default_value=1),
        "model_trainig_config": {
            "optimizer": Field(
                str,
                description="Type of optimizer to use",
                is_required=False,
                default_value="adam",
            ),
            "loss": Field(str, is_required=False, default_value="mse"),
            "num_epochs": Field(int, description="Number of epochs to optimize over"),
        },
    },
    input_defs=[
        InputDefinition("training_set", dagster_type=TrainingSet),
        InputDefinition("bucket_name", dagster_type=str),
    ],
    output_defs=[OutputDefinition(Any)],
    required_resource_keys={"gcs_client"},
)
def train_lstm_model_and_upload_to_gcs(context, training_set: TrainingSet, bucket_name: str):
    X, y = training_set
    breakpoint = context.solid_config["timeseries_train_test_breakpoint"]  # pylint: disable=W0622
    X_train, X_test = X[0:breakpoint], X[breakpoint:]
    y_train, y_test = y[0:breakpoint], y[breakpoint:]

    _, n_steps, n_features = X.shape
    model = Sequential()
    model.add(
        LSTM(
            context.solid_config["lstm_layer_config"]["num_recurrant_units"],
            activation=context.solid_config["lstm_layer_config"]["activation"],
            input_shape=(n_steps, n_features),
        )
    )
    model.add(Dense(context.solid_config["num_dense_layers"]))
    model.compile(
        optimizer=context.solid_config["model_trainig_config"]["optimizer"],
        loss=context.solid_config["model_trainig_config"]["loss"],
        metrics=["mae"],
    )
    model.fit(
        X_train,
        y_train,
        epochs=context.solid_config["model_trainig_config"]["num_epochs"],
        verbose=0,
    )
    results = model.evaluate(X_test, y_test, verbose=0)

    # save model and upload
    gcs_bucket = context.resources.gcs_client.get_bucket(bucket_name)
    key = "model-{}.h5".format(uuid.uuid4())
    with tempfile.TemporaryFile("w+b") as fp:
        model.save(fp)
        # Done because you can't upload the contents of a file outside the context manager if it's a tempfile.
        fp.seek(0)
        gcs_bucket.blob(key).upload_from_file(fp)

    gcs_url = "gs://{bucket_name}/{key}".format(bucket_name=bucket_name, key=key)
    yield AssetMaterialization(
        asset_key=gcs_url,
        description="Serialized model to Google Cloud Storage Bucket",
        metadata_entries=[
            EventMetadataEntry.text(gcs_url, "google cloud storage URI"),
            EventMetadataEntry.text(str(results[0]), "Mean Squared Error"),
            EventMetadataEntry.text(str(results[1]), "Mean Absolute Error"),
        ],
    )
    yield Output(model)


@composite_solid(output_defs=[OutputDefinition(str, "trip_table_name")])
def trip_etl():
    download_baybike_zipfile_from_url = download_zipfile_from_url.alias(
        "download_baybike_zipfile_from_url"
    )
    insert_trip_data_into_table = insert_into_staging_table.alias("insert_trip_data_into_table")
    load_baybike_data_into_dataframe = load_compressed_csv_file.alias(
        "load_baybike_data_into_dataframe"
    )
    return insert_trip_data_into_table(
        load_baybike_data_into_dataframe(download_baybike_zipfile_from_url())
    )


@composite_solid(
    input_defs=[InputDefinition("trip_table_name", str)],
    output_defs=[OutputDefinition(name="trip_dataframe", dagster_type=TripDataFrame)],
)
def produce_trip_dataset(trip_table_name: str) -> DataFrame:
    load_entire_trip_table = create_download_table_as_dataframe_solid(
        "load_entire_trip_table", RawTripDataFrame
    )
    return preprocess_trip_dataset(load_entire_trip_table(trip_table_name))


@composite_solid(output_defs=[OutputDefinition(str, "weather_table_name")])
def weather_etl():
    insert_weather_report_into_table = insert_into_staging_table.alias(
        "insert_weather_report_into_table"
    )
    return insert_weather_report_into_table(download_weather_report_from_weather_api())


@composite_solid(
    input_defs=[InputDefinition("weather_table_name", str)],
    output_defs=[OutputDefinition(name="weather_dataframe", dagster_type=WeatherDataFrame)],
)
def produce_weather_dataset(weather_table_name: str) -> DataFrame:
    load_entire_weather_table = create_download_table_as_dataframe_solid(
        "load_entire_weather_table", DagsterPandasDataFrame
    )
    return preprocess_weather_dataset(load_entire_weather_table(weather_table_name))


@composite_solid(
    input_defs=[
        InputDefinition("weather_table_name", str),
        InputDefinition("trip_table_name", str),
    ],
)
def train_daily_bike_supply_model(weather_table_name: str, trip_table_name: str):
    upload_training_set_to_gcs = upload_pickled_object_to_gcs_bucket.alias(
        "upload_training_set_to_gcs"
    )
    return train_lstm_model_and_upload_to_gcs(
        upload_training_set_to_gcs(
            produce_training_set(
                transform_into_traffic_dataset(produce_trip_dataset(trip_table_name)),
                produce_weather_dataset(weather_table_name),
            )
        )
    )
