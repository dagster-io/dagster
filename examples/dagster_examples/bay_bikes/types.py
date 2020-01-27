from dagster_pandas.data_frame import create_dagster_pandas_dataframe_type
from dagster_pandas.validation import PandasColumn
from numpy import mean, median, ndarray
from pandas import Timestamp

from dagster import DagsterType, EventMetadataEntry, TypeCheck


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


def compute_trip_dataframe_event_metadata(dataframe):
    return [
        EventMetadataEntry.text(
            str(min(dataframe['start_time'])), 'min_start_time', 'Date data collection started',
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
    ]


TripDataFrameSchema = [
    PandasColumn.integer_column('bike_id', min_value=0),
    PandasColumn.datetime_column('start_time', min_datetime=Timestamp(year=2018, month=1, day=1),),
    PandasColumn.datetime_column('end_time', min_datetime=Timestamp(year=2018, month=1, day=1),),
    PandasColumn.string_column('interval_date'),
]


RawTripDataFrame = create_dagster_pandas_dataframe_type(
    name='RawTripDataFrame',
    columns=[
        PandasColumn(column.name)
        for column in TripDataFrameSchema
        if column.name != 'interval_date'
    ],
)


TripDataFrame = create_dagster_pandas_dataframe_type(
    name='TripDataFrame',
    columns=TripDataFrameSchema,
    event_metadata_fn=compute_trip_dataframe_event_metadata,
)


def compute_traffic_dataframe_event_metadata(dataframe):
    return [
        EventMetadataEntry.text(
            str(min(dataframe['peak_traffic_load'])), 'min_traffic_load', 'Best Peak Load'
        ),
        EventMetadataEntry.text(
            str(max(dataframe['peak_traffic_load'])), 'max_traffic_load', 'Worst Peak Load'
        ),
        EventMetadataEntry.text(
            str(mean(dataframe['peak_traffic_load'])), 'mean_traffic_load', 'Mean peak traffic',
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
    ]


TrafficDataFrame = create_dagster_pandas_dataframe_type(
    name='TrafficDataFrame',
    columns=[
        PandasColumn.string_column('interval_date'),
        PandasColumn.integer_column('peak_traffic_load', min_value=0),
    ],
    event_metadata_fn=compute_traffic_dataframe_event_metadata,
)


def compute_weather_dataframe_event_metadata(dataframe):
    return [
        EventMetadataEntry.text(
            str(len(dataframe)), 'n_rows', 'Number of rows seen in the dataframe'
        ),
        EventMetadataEntry.text(
            str(dataframe.columns), 'columns', 'Keys of columns seen in the dataframe'
        ),
    ]


RawWeatherDataFrameSchema = [
    PandasColumn.integer_column('time', unique=True),
    PandasColumn.categorical_column(
        'summary',
        categories={
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
        },
    ),
    PandasColumn.categorical_column(
        'icon', categories={'clear-day', 'cloudy', 'fog', 'partly-cloudy-day', 'rain'}
    ),
    PandasColumn.integer_column('sunriseTime', min_value=0),
    PandasColumn.integer_column('sunsetTime', min_value=0),
    PandasColumn.float_column('precipIntensity', min_value=0.0, max_value=1.0),
    PandasColumn.float_column('precipIntensityMax', min_value=0.0, max_value=1.0),
    PandasColumn.float_column('precipProbability', min_value=0.0, max_value=1.0),
    PandasColumn.float_column('temperatureHigh', min_value=40.0, max_value=100.0),
    PandasColumn.integer_column('temperatureHighTime', min_value=0),
    PandasColumn.float_column('temperatureLow', min_value=30.0, max_value=100.0),
    PandasColumn.integer_column('temperatureLowTime', min_value=0),
    PandasColumn.float_column('dewPoint', min_value=10.0, max_value=70.0),
    PandasColumn.float_column('humidity', min_value=0.0, max_value=1.0),
    PandasColumn.float_column('pressure', min_value=900.0, max_value=1200.0),
    PandasColumn.float_column('windSpeed', min_value=0.0, max_value=17.0),
    PandasColumn.float_column('windGust', min_value=0.0, max_value=40.0),
    PandasColumn.integer_column('windGustTime', min_value=0),
    PandasColumn.integer_column('windBearing', min_value=1, max_value=400),
    PandasColumn.float_column('cloudCover', min_value=0.0, max_value=1.0),
    PandasColumn.integer_column('uvIndex', min_value=0, max_value=12),
    PandasColumn.integer_column('uvIndexTime', min_value=0),
    PandasColumn.float_column('visibility', min_value=0.0, max_value=10.0),
    PandasColumn.float_column('ozone', min_value=200.0, max_value=500.0),
]

WeatherDataFrameSchema = RawWeatherDataFrameSchema + [
    PandasColumn.boolean_column('didRain', exists=True),
]

RawWeatherDataFrame = create_dagster_pandas_dataframe_type(
    name='RawWeatherDataFrame', columns=RawWeatherDataFrameSchema,
)

WeatherDataFrame = create_dagster_pandas_dataframe_type(
    name='WeatherDataFrame',
    columns=WeatherDataFrameSchema,
    event_metadata_fn=compute_weather_dataframe_event_metadata,
)


def validate_snapshot_timeseries(training_set_data):
    if not isinstance(training_set_data, tuple):
        return TypeCheck(False)

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


TrainingSet = DagsterType(
    name='TrainingSet',
    key='TrainingSet',
    description='Final training set ready for the ml pipeline',
    type_check_fn=validate_snapshot_timeseries,
)
