import os
import uuid
import zipfile
from datetime import timedelta
from time import gmtime, strftime
from typing import Tuple

import requests
from dagster_examples.bay_bikes.constants import (
    DARK_SKY_BASE_URL,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    WEATHER_COLUMNS,
)
from dagster_examples.bay_bikes.types import (
    RawTripDataFrame,
    RawWeatherDataFrame,
    TrafficDataFrame,
    TrainingSet,
    TripDataFrame,
    WeatherDataFrame,
)
from keras.layers import LSTM, Dense
from keras.models import Sequential
from numpy import array, ndarray, transpose
from pandas import DataFrame, concat, date_range, get_dummies, read_csv, to_datetime

from dagster import (
    Any,
    EventMetadataEntry,
    Field,
    InputDefinition,
    List,
    Materialization,
    Output,
    OutputDefinition,
    check,
    composite_solid,
    solid,
)

# Added this to silence tensorflow logs. They are insanely verbose.
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


def _write_chunks_to_fp(response, output_fp, chunk_size):
    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            output_fp.write(chunk)


def _download_zipfile_from_url(url: str, target: str, chunk_size=8192) -> str:
    with requests.get(url, stream=True) as response, open(target, 'wb+') as output_fp:
        response.raise_for_status()
        _write_chunks_to_fp(response, output_fp, chunk_size)
    return target


@solid(
    config={'chunk_size': Field(int, is_required=False, default_value=8192)},
    required_resource_keys={'volume'},
)
def download_zipfiles_from_urls(
    context, base_url: str, file_names: List[str], target_dir: str
) -> List[str]:
    # mount dirs onto volume
    zipfile_location = os.path.join(context.resources.volume, target_dir)
    if not os.path.exists(zipfile_location):
        os.mkdir(zipfile_location)
    for file_name in file_names:
        if not os.path.exists(os.path.join(zipfile_location, file_name)):
            _download_zipfile_from_url(
                "/".join([base_url, file_name]),
                os.path.join(zipfile_location, file_name),
                context.solid_config['chunk_size'],
            )
    return file_names


def _unzip_file(zipfile_path: str, target: str) -> str:
    with zipfile.ZipFile(zipfile_path, 'r') as zip_fp:
        zip_fp.extractall(target)
        return zip_fp.namelist()[0]


@solid(required_resource_keys={'volume'})
def unzip_files(context, file_names: List[str], source_dir: str, target_dir: str) -> List[str]:
    # mount dirs onto volume
    zipfile_location = os.path.join(context.resources.volume, source_dir)
    csv_location = os.path.join(context.resources.volume, target_dir)
    if not os.path.exists(csv_location):
        os.mkdir(csv_location)
    return [
        _unzip_file(os.path.join(zipfile_location, file_name), csv_location)
        for file_name in file_names
    ]


@solid(
    config={
        'delimiter': Field(
            str,
            default_value=',',
            is_required=False,
            description=('A one-character string used to separate fields.'),
        )
    },
    required_resource_keys={'volume'},
)
def consolidate_csv_files(context, input_file_names: List[str], source_dir: str) -> DataFrame:
    # mount dirs onto volume
    csv_file_location = os.path.join(context.resources.volume, source_dir)
    if not os.path.exists(csv_file_location):
        os.mkdir(csv_file_location)
    # There must be a header in all of these dataframes or pandas won't know how to concatinate dataframes.
    dataset = concat(
        [
            read_csv(
                os.path.join(csv_file_location, file_name),
                sep=context.solid_config['delimiter'],
                header=0,
            )
            for file_name in input_file_names
        ]
    )
    return dataset


@solid(required_resource_keys={'transporter'})
def upload_file_to_bucket(context, path_to_file: str, key: str):
    context.resources.transporter.upload_file_to_bucket(path_to_file, key)


@solid(required_resource_keys={'transporter', 'volume'})
def download_csv_from_bucket_and_return_dataframe(
    context, key: str, path_to_file: str
) -> DataFrame:
    target_csv_location = os.path.join(context.resources.volume, path_to_file)
    context.resources.transporter.download_file_from_bucket(key, target_csv_location)
    return read_csv(target_csv_location)


@solid(config={'index_label': Field(str),}, required_resource_keys={'postgres_db'})
def insert_row_into_table(context, row: DataFrame, table_name: str):
    row.to_sql(
        table_name,
        context.resources.postgres_db.engine,
        if_exists='append',
        index=False,
        index_label=context.solid_config['index_label'],
    )


@solid(
    config={
        'latitude': Field(
            float,
            default_value=37.8267,
            is_required=False,
            description=('Latitude coordinate to get weather data about. Default is SF.'),
        ),
        'longitude': Field(
            float,
            default_value=-122.4233,
            is_required=False,
            description=('Longitude coordinate to get weather data about. Default is SF.'),
        ),
        'times_to_exclude': Field(
            [str],
            default_value=['currently', 'minutely', 'hourly', 'alerts', 'flags'],
            is_required=False,
            description='data granularities to exclude when making this api call',
        ),
    },
    required_resource_keys={'credentials_vault'},
)
def download_weather_report_from_weather_api(context, epoch_date: int) -> DataFrame:
    # Make API Call
    coordinates = '{0},{1}'.format(
        context.solid_config['latitude'], context.solid_config['longitude']
    )
    weather_api_key = context.resources.credentials_vault.credentials["DARK_SKY_API_KEY"]
    url_prefix = '/'.join([DARK_SKY_BASE_URL, weather_api_key, coordinates])
    url = url_prefix + ',{}?exclude={}'.format(
        epoch_date, ','.join(context.solid_config['times_to_exclude'])
    )
    context.log.info("Sending Request. URL is: {}".format(url))
    response = requests.get(url)
    response.raise_for_status()
    raw_weather_data = response.json()['daily']['data'][0]
    raw_weather_data['uuid'] = uuid.uuid4()
    return DataFrame([raw_weather_data])


@solid(
    input_defs=[InputDefinition(name='dataframe', dagster_type=RawTripDataFrame)],
    output_defs=[OutputDefinition(name='trip_dataframe', dagster_type=TripDataFrame)],
)
def preprocess_trip_dataset(_, dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe[['bike_id', 'start_time', 'end_time']].dropna(how='all').reindex()
    dataframe['bike_id'] = dataframe['bike_id'].astype('int64')
    dataframe['start_time'] = to_datetime(dataframe['start_time'])
    dataframe['end_time'] = to_datetime(dataframe['end_time'])
    dataframe['interval_date'] = dataframe['start_time'].apply(lambda x: x.date())
    yield Output(dataframe, output_name='trip_dataframe')


@composite_solid(output_defs=[OutputDefinition(name='trip_dataframe', dagster_type=TripDataFrame)])
def produce_trip_dataset():
    download_baybike_zipfiles_from_url = download_zipfiles_from_urls.alias(
        'download_baybike_zipfiles_from_url'
    )
    unzip_baybike_zipfiles = unzip_files.alias('unzip_baybike_zipfiles')
    consolidate_baybike_data_into_trip_dataset = consolidate_csv_files.alias(
        'consolidate_baybike_data_into_trip_dataset'
    )

    return preprocess_trip_dataset(
        consolidate_baybike_data_into_trip_dataset(
            unzip_baybike_zipfiles(download_baybike_zipfiles_from_url())
        )
    )


@solid(
    input_defs=[InputDefinition(name='dataframe', dagster_type=RawWeatherDataFrame)],
    output_defs=[OutputDefinition(name='weather_dataframe', dagster_type=WeatherDataFrame)],
)
def preprocess_weather_dataset(_, dataframe: DataFrame) -> DataFrame:
    '''
    Steps:

    1. Converts time columns to match the date types in the traffic dataset so
    that we can join effectively.

    2. Fills N/A values in ozone, so that we have the right datatypes.

    3. Convert precipType to a column that's more amenable to one hot encoding.
    '''
    dataframe = dataframe[WEATHER_COLUMNS].dropna(how='all').reindex()
    # These are to address weird corner cases where columns are NA
    # This fill is because the weather API fails to have a summary for certain types of clear days.
    dataframe['summary'] = dataframe['summary'].fillna('Clear throughout the day.')
    dataframe['icon'] = dataframe['icon'].fillna('clear-day')
    # This happens frequently, I defaulted to the average.
    dataframe['temperatureLow'] = dataframe['temperatureLow'].fillna(
        dataframe.temperatureLow.mean()
    )
    # This happens frequently as well, I defaulted to the median since this is a time datatype
    dataframe['temperatureLowTime'] = (
        dataframe['temperatureLowTime']
        .fillna(dataframe.temperatureLowTime.median())
        .astype('int64')
    )
    # This happens frequently, the median felt like the appropriate statistic. Can change this over time.
    dataframe['ozone'] = dataframe['ozone'].fillna(dataframe.ozone.median())
    dataframe['time'] = to_datetime(
        dataframe['time'].apply(lambda epoch_ts: strftime('%Y-%m-%d', gmtime(epoch_ts)))
    )
    dataframe['didRain'] = dataframe.precipType.apply(lambda x: x == 'rain')
    del dataframe['precipType']
    yield Output(dataframe, output_name='weather_dataframe')


@composite_solid(
    output_defs=[OutputDefinition(name='weather_dataframe', dagster_type=WeatherDataFrame)]
)
def produce_weather_dataset() -> DataFrame:
    download_weather_dataset = download_csv_from_bucket_and_return_dataframe.alias(
        'download_weather_dataset'
    )
    return preprocess_weather_dataset(download_weather_dataset())


@solid(
    input_defs=[InputDefinition('trip_dataset', dagster_type=TripDataFrame)],
    output_defs=[OutputDefinition(name='traffic_dataframe', dagster_type=TrafficDataFrame)],
)
def transform_into_traffic_dataset(_, trip_dataset: DataFrame) -> DataFrame:
    def max_traffic_load(trips):
        interval_count = {
            start_interval: 0 for start_interval in date_range(trips.name, periods=24, freq='h')
        }
        for interval in interval_count.keys():
            upper_bound_interval = interval + timedelta(hours=1)
            # Count number of bikes in transit during sample interval
            interval_count[interval] = len(
                trips[
                    (
                        (  # Select trip if the trip started within the sample interval
                            (interval <= trips['start_time'])
                            & (trips['start_time'] < upper_bound_interval)
                        )
                        | (  # Select trip if the trip ended within the sample interval
                            (interval <= trips['end_time'])
                            & (trips['end_time'] < upper_bound_interval)
                        )
                        | (  # Select trip if the trip started AND ended outside of the interval
                            (trips['start_time'] < interval)
                            & (trips['end_time'] >= upper_bound_interval)
                        )
                    )
                ]
            )
        return max(interval_count.values())

    counts = trip_dataset.groupby(['interval_date']).apply(max_traffic_load)
    traffic_dataset = DataFrame(counts).reset_index()
    traffic_dataset.columns = ['interval_date', 'peak_traffic_load']
    yield Output(traffic_dataset, output_name='traffic_dataframe')


class Timeseries:
    def __init__(self, sequence):
        self.sequence = check.opt_list_param(sequence, 'sequence', of_type=(int, float))

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
                input_sequences, 'input_sequences', of_type=elem_type
            )
        ]
        self.output_timeseries = Timeseries(check.list_param(output_sequence, 'output_sequence'))
        if len(input_sequence_names) != len(self.input_timeseries_collection):
            raise ValueError("Every timeseries needs a name attached to it.")
        self.input_timeseries_names = check.list_param(
            input_sequence_names, 'input_sequence_names', of_type=str
        )
        self.output_timeseries_name = check.str_param(output_sequence_name, 'output_sequence_name')

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
    config={'memory_length': Field(int, description='The window memory length')},
    input_defs=[
        InputDefinition('traffic_dataset', dagster_type=TrafficDataFrame),
        InputDefinition('weather_dataset', dagster_type=WeatherDataFrame),
    ],
    output_defs=[OutputDefinition(dagster_type=TrainingSet)],
)
def produce_training_set(
    context, traffic_dataset: DataFrame, weather_dataset: DataFrame
) -> Tuple[ndarray, ndarray]:
    traffic_dataset['time'] = to_datetime(traffic_dataset.interval_date)
    weather_dataset['time'] = to_datetime(weather_dataset.time)
    dataset = traffic_dataset.join(weather_dataset.set_index('time'), on='time')
    dataset = get_dummies(dataset, columns=['summary', 'icon', 'didRain'])
    multivariate_timeseries = MultivariateTimeseries.from_dataframe(
        dataset, FEATURE_COLUMNS, LABEL_COLUMN
    )
    input_snapshot_matrix, output = multivariate_timeseries.convert_to_snapshot_matrix(
        context.solid_config['memory_length']
    )
    return input_snapshot_matrix, output


@solid(
    config={
        'timeseries_train_test_breakpoint': Field(
            int, description='The breakpoint between training and test set'
        ),
        'lstm_layer_config': {
            'activation': Field(str, is_required=False, default_value='relu'),
            'num_recurrant_units': Field(int, is_required=False, default_value=50),
        },
        'num_dense_layers': Field(int, is_required=False, default_value=1),
        'model_trainig_config': {
            'optimizer': Field(
                str,
                description='Type of optimizer to use',
                is_required=False,
                default_value='adam',
            ),
            'loss': Field(str, is_required=False, default_value='mse'),
            'num_epochs': Field(int, description='Number of epochs to optimize over'),
        },
    },
    input_defs=[InputDefinition('training_set', dagster_type=TrainingSet)],
    output_defs=[OutputDefinition(Any)],
)
def train_lstm_model(context, training_set: TrainingSet):
    X, y = training_set
    breakpoint = context.solid_config['timeseries_train_test_breakpoint']  # pylint: disable=W0622
    X_train, X_test = X[0:breakpoint], X[breakpoint:]
    y_train, y_test = y[0:breakpoint], y[breakpoint:]

    _, n_steps, n_features = X.shape
    model = Sequential()
    model.add(
        LSTM(
            context.solid_config['lstm_layer_config']['num_recurrant_units'],
            activation=context.solid_config['lstm_layer_config']['activation'],
            input_shape=(n_steps, n_features),
        )
    )
    model.add(Dense(context.solid_config['num_dense_layers']))
    model.compile(
        optimizer=context.solid_config['model_trainig_config']['optimizer'],
        loss=context.solid_config['model_trainig_config']['loss'],
        metrics=['mae'],
    )
    model.fit(
        X_train,
        y_train,
        epochs=context.solid_config['model_trainig_config']['num_epochs'],
        verbose=0,
    )
    results = model.evaluate(X_test, y_test, verbose=0)
    yield Materialization(
        label='test_set_results',
        metadata_entries=[
            EventMetadataEntry.text(str(results[0]), 'Mean Squared Error'),
            EventMetadataEntry.text(str(results[1]), 'Mean Absolute Error'),
        ],
    )
    yield Output(model)
