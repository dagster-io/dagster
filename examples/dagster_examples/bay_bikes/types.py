from numpy import mean, median, ndarray
from pandas import DataFrame, Timestamp

from dagster import EventMetadataEntry, TypeCheck, dagster_type


class ValidationTypes(object):
    CATEGORIES = 'categories'
    EXPECTED_DTYPES = 'expected_dtypes'
    BOUNDS = 'bounds'
    NO_DUPLICATES = 'no_duplicates'


class DataFrameValidator(object):
    def __init__(self, invariant_config):
        self.invariant_config = invariant_config

    def validate_columns_in_dataframe(self, dataframe):
        for mandatory_column_name, mandatory_column_config in self.invariant_config.items():
            if mandatory_column_name not in dataframe.columns:
                return TypeCheck(
                    success=False,
                    description='Dataframe should have {} columns. Currently missing {}'.format(
                        self.invariant_config.keys(), mandatory_column_name
                    ),
                )
            if ValidationTypes.CATEGORIES in mandatory_column_config:
                valid_column_mask = dataframe[mandatory_column_name].isin(
                    mandatory_column_config[ValidationTypes.CATEGORIES]
                )
                valid_columns = dataframe.loc[valid_column_mask]
                if len(dataframe) != len(valid_columns):
                    return TypeCheck(
                        success=False,
                        description=(
                            'Dataframe column {column} expects the following buckets {valid_buckets}. '
                            'Found other values instead.'.format(
                                column=mandatory_column_name,
                                valid_buckets=mandatory_column_config[ValidationTypes.CATEGORIES],
                            )
                        ),
                    )
            if ValidationTypes.EXPECTED_DTYPES in mandatory_column_config:
                if (
                    str(dataframe[mandatory_column_name].dtype)
                    not in mandatory_column_config[ValidationTypes.EXPECTED_DTYPES]
                ):
                    return TypeCheck(
                        success=False,
                        description='Dataframe column {column} expects {expected} dtypes. Got {received} instead'.format(
                            column=mandatory_column_name,
                            expected=str(mandatory_column_config[ValidationTypes.EXPECTED_DTYPES]),
                            received=dataframe[mandatory_column_name].dtype,
                        ),
                    )
            if ValidationTypes.BOUNDS in mandatory_column_config:
                bounds_mask = dataframe[mandatory_column_name].between(
                    mandatory_column_config[ValidationTypes.BOUNDS][0],
                    mandatory_column_config[ValidationTypes.BOUNDS][1],
                )
                out_of_bounds_records = dataframe[mandatory_column_name][~bounds_mask]
                if len(out_of_bounds_records) > 0:
                    return TypeCheck(
                        success=False,
                        description=(
                            'Dataframe column {column} expects values between {min_}-{max_}.'
                            'The following (row number, value) pairs violate this: {errors}'
                        ).format(
                            column=mandatory_column_name,
                            min_=mandatory_column_config['bounds'][0],
                            max_=mandatory_column_config['bounds'][1],
                            errors=out_of_bounds_records,
                        ),
                    )
            if ValidationTypes.NO_DUPLICATES in mandatory_column_config:
                if len(dataframe[mandatory_column_name]) != len(
                    dataframe[mandatory_column_name].unique()
                ):
                    return TypeCheck(
                        success=False,
                        description='Trip Dataframe has duplicates for column {}. Please dedup'.format(
                            mandatory_column_name
                        ),
                    )


def validate_trip_dataframe(dataframe):
    TRIP_CONFIG = {
        'bike_id': {'bounds': (0, float('inf')), 'expected_dtypes': {'int64'}},
        'start_time': {
            'bounds': (Timestamp(year=2018, month=1, day=1), Timestamp(year=2020, month=1, day=1)),
            'expected_dtypes': {'<M8[ns]', 'datetime64[ns]'},
        },
        'end_time': {
            'bounds': (Timestamp(year=2018, month=1, day=1), Timestamp(year=2020, month=1, day=1)),
            'expected_dtypes': {'<M8[ns]', 'datetime64[ns]'},
        },
        'interval_date': {'expected_dtypes': {'str', 'object'}},
    }
    failed_type_check = DataFrameValidator(TRIP_CONFIG).validate_columns_in_dataframe(dataframe)
    return (
        failed_type_check
        if failed_type_check
        else TypeCheck(
            success=True,
            metadata_entries=[
                EventMetadataEntry.text(
                    str(min(dataframe['start_time'])),
                    'min_start_time',
                    'Date data collection started',
                ),
                EventMetadataEntry.text(
                    str(max(dataframe['end_time'])), 'max_end_time', 'Timestamp of last trip'
                ),
                EventMetadataEntry.text(
                    str(len(dataframe)), 'n_rows', 'Number of rows seen in the dataframe'
                ),
                EventMetadataEntry.text(
                    str(dataframe.columns), 'columns', 'Keys of columns seen in the dataframe'
                ),
            ],
        )
    )


@dagster_type(  # pylint: disable=W0223
    name='TripDataFrame',
    description='A consolidated view of all bay bike trips in 2018/2019',
    type_check=validate_trip_dataframe,
)
class TripDataFrame(DataFrame):
    pass


def validate_traffic_dataframe(dataframe):
    TRAFFIC_CONFIG = {
        'interval_date': {'expected_dtypes': {'str', 'object'}},
        'peak_traffic_load': {'bounds': (0, float('inf')), 'expected_dtypes': {'int64'}},
    }
    failed_type_check = DataFrameValidator(TRAFFIC_CONFIG).validate_columns_in_dataframe(dataframe)
    return (
        failed_type_check
        if failed_type_check
        else TypeCheck(
            success=True,
            description='Yay',
            metadata_entries=[
                EventMetadataEntry.text(
                    str(min(dataframe['peak_traffic_load'])), 'min_traffic_load', 'Best Peak Load'
                ),
                EventMetadataEntry.text(
                    str(max(dataframe['peak_traffic_load'])), 'max_traffic_load', 'Worst Peak Load'
                ),
                EventMetadataEntry.text(
                    str(mean(dataframe['peak_traffic_load'])),
                    'mean_traffic_load',
                    'Mean peak traffic',
                ),
                EventMetadataEntry.text(
                    str(median(dataframe['peak_traffic_load'])),
                    'median_traffic_load',
                    'Median peak traffic',
                ),
                EventMetadataEntry.text(
                    str(len(dataframe)), 'n_rows', 'Number of rows seen in the dataframe'
                ),
                EventMetadataEntry.text(
                    str(dataframe.columns), 'columns', 'Keys of columns seen in the dataframe'
                ),
            ],
        )
    )


@dagster_type(  # pylint: disable=W0223
    name='TrafficDataFrame',
    description='A consolidated view of peak traffic for each day in 2018/2019',
    type_check=validate_traffic_dataframe,
)
class TrafficDataFrame(DataFrame):
    pass


def validate_weather_dataframe(dataframe):
    WEATHER_CONFIG = {
        'time': {
            'bounds': (Timestamp(year=2018, month=1, day=1), Timestamp(year=2020, month=1, day=1)),
            'expected_dtypes': {'<M8[ns]', 'datetime64[ns]'},
            'no_duplicates': None,
        },
        'summary': {
            'categories': {
                'Partly cloudy throughout the day.',
                'Mostly cloudy throughout the day.',
                'Clear throughout the day.',
                'Light rain in the morning and afternoon.',
                'Light rain starting in the afternoon.',
                'Rain throughout the day.',
                'Overcast throughout the day.',
                'Foggy in the morning and afternoon.',
                'Light rain in the morning.',
                'Possible drizzle in the morning.',
                'Light rain throughout the day.',
                'Possible drizzle in the evening and overnight.',
                'Rain starting in the afternoon.',
                'Light rain until morning, starting again in the evening.',
                'Foggy starting in the afternoon.',
                'Light rain in the morning and overnight.',
                'Light rain overnight.',
                'Light rain in the evening and overnight.',
                'Drizzle in the morning and afternoon.',
                'Rain overnight.',
                'Light rain until evening.',
                'Possible drizzle in the morning and afternoon.',
                'Possible drizzle overnight.',
                'Light rain in the afternoon and evening.',
                'Drizzle in the afternoon and evening.',
                'Rain until morning, starting again in the evening.',
                'Drizzle until morning, starting again in the evening.',
                'Possible drizzle in the afternoon and evening.',
                'Foggy throughout the day.',
                'Possible drizzle until morning, starting again in the evening.',
                'Foggy until evening.',
                'Possible light rain until evening.',
                'Foggy in the morning.',
                'Rain until evening.',
                'Drizzle starting in the afternoon.',
                'Rain in the morning and afternoon.',
                'Possible drizzle throughout the day.',
                'Heavy rain until morning, starting again in the evening.',
                'Foggy overnight.',
                'Rain in the evening and overnight.',
                'Rain in the morning.',
            }
        },
        'icon': {'categories': {'clear-day', 'cloudy', 'fog', 'partly-cloudy-day', 'rain'}},
        'sunriseTime': {'bounds': [0, float('inf')], 'expected_dtypes': {'int64'}},
        'sunsetTime': {'bounds': [0, float('inf')], 'expected_dtypes': {'int64'}},
        'precipIntensity': {'bounds': [0, 1], 'expected_dtypes': {'float64'}},
        'precipIntensityMax': {'bounds': [0, 1], 'expected_dtypes': {'float64'}},
        'precipProbability': {'bounds': [0, 1], 'expected_dtypes': {'float64'}},
        'temperatureHigh': {'bounds': [40, 100], 'expected_dtaypes': {'float64'}},
        'temperatureHighTime': {'bounds': [0, float('inf')], 'expected_dtypes': {'int64'}},
        'temperatureLow': {'bounds': [30, 100], 'expected_dtaypes': {'float64'}},
        'temperatureLowTime': {'bounds': [0, float('inf')], 'expected_dtypes': {'int64'}},
        'dewPoint': {'bounds': [10, 70], 'expected_dtypes': {'float64'}},
        'humidity': {'bounds': [0, 1], 'expected_dtypes': {'float64'}},
        'pressure': {'bounds': [900, 1200], 'expected_dtypes': {'float64'}},
        'windSpeed': {'bounds': [0, 17], 'expected_dtypes': {'float64'}},
        'windGust': {'bounds': [0, 40], 'expected_dtypes': {'float64'}},
        'windGustTime': {'bounds': [0, float('inf')], 'expected_dtypes': {'int64'}},
        'windBearing': {'bounds': [1, 400], 'expected_dtypes': {'int64'}},
        'cloudCover': {'bounds': [0, 1], 'expected_dtypes': {'float64'}},
        'uvIndex': {'bounds': [0, 12], 'expected_dtypes': {'int64'}},
        'uvIndexTime': {'bounds': [0, float('inf')], 'expected_dtypes': {'int64'}},
        'visibility': {'bounds': [0, 10], 'expected_dtypes': {'float64'}},
        'ozone': {'bounds': [200, 500], 'expected_dtypes': {'float64'}},
        'didRain': {'categories': {True, False}},
    }
    failed_type_check = DataFrameValidator(WEATHER_CONFIG).validate_columns_in_dataframe(dataframe)
    return (
        failed_type_check
        if failed_type_check
        else TypeCheck(
            success=True,
            metadata_entries=[
                EventMetadataEntry.text(
                    str(len(dataframe)), 'n_rows', 'Number of rows seen in the dataframe'
                ),
                EventMetadataEntry.text(
                    str(dataframe.columns), 'columns', 'Keys of columns seen in the dataframe'
                ),
            ],
        )
    )


@dagster_type(  # pylint: disable=W0223
    name='WeatherDataFrame',
    description='A consolidated summary of bay area weather for each day in 2018/2019',
    type_check=validate_weather_dataframe,
)
class WeatherDataFrame(DataFrame):
    pass


def validate_snapshot_timeseries(training_set_data):
    if len(training_set_data) != 2:
        return TypeCheck(
            success=False,
            description='Invalid training set. The tuple must consist of a training set, output vector, and feature_names',
        )
    # tuple argument types
    X, y = training_set_data
    if not (isinstance(X, ndarray) and isinstance(y, ndarray)):
        return TypeCheck(
            success=False,
            description='Both input matrix and output vector must be numpy arrays. X: {} | y: {}'.format(
                type(X), type(y)
            ),
        )

    timeseries_length, snapshot_length, num_timeseries = X.shape
    output_vector_length = y.shape[0]
    if num_timeseries == 0 or output_vector_length == 0:
        return TypeCheck(success=False, description='No empty training sets allowed',)

    if timeseries_length != output_vector_length:
        return TypeCheck(
            success=False, description='Every timeseries must have as many snapshots as outputs'
        )

    return TypeCheck(
        success=True,
        metadata_entries=[
            EventMetadataEntry.text(
                str(num_timeseries), 'num_ts', 'Number of parallel timeseries.'
            ),
            EventMetadataEntry.text(
                str(timeseries_length), 'timeseries_length', 'Length of each timeseries.'
            ),
            EventMetadataEntry.text(
                str(snapshot_length),
                'snapshot_length',
                'Number of past observations for each input.',
            ),
        ],
    )


@dagster_type(
    name='TrainingSet',
    description='Final training set ready for the ml pipeline',
    type_check=validate_snapshot_timeseries,
)
class TrainingSet(tuple):
    pass
