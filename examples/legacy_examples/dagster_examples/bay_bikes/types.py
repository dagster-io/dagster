from dagster import DagsterType, EventMetadataEntry, TypeCheck
from dagster_pandas.data_frame import create_dagster_pandas_dataframe_type
from dagster_pandas.validation import PandasColumn
from numpy import mean, median, ndarray
from pandas import Timestamp


def compute_trip_dataframe_event_metadata(dataframe):
    return [
        EventMetadataEntry.text(
            str(min(dataframe["start_time"])),
            "min_start_time",
            "Date data collection started",
        ),
        EventMetadataEntry.text(
            str(max(dataframe["end_time"])), "max_end_time", "Timestamp of last trip"
        ),
        EventMetadataEntry.text(
            str(len(dataframe)), "n_rows", "Number of rows seen in the dataframe"
        ),
        EventMetadataEntry.text(
            str(dataframe.columns), "columns", "Keys of columns seen in the dataframe"
        ),
    ]


TripDataFrameSchema = [
    PandasColumn.integer_column("bike_id", min_value=0),
    PandasColumn.datetime_column(
        "start_time",
        min_datetime=Timestamp(year=2017, month=1, day=1),
    ),
    PandasColumn.datetime_column(
        "end_time",
        min_datetime=Timestamp(year=2017, month=1, day=1),
    ),
    PandasColumn.string_column("interval_date"),
]


RawTripDataFrame = create_dagster_pandas_dataframe_type(
    name="RawTripDataFrame",
    columns=[
        PandasColumn(column.name)
        for column in TripDataFrameSchema
        if column.name != "interval_date"
    ],
)


TripDataFrame = create_dagster_pandas_dataframe_type(
    name="TripDataFrame",
    columns=TripDataFrameSchema,
    event_metadata_fn=compute_trip_dataframe_event_metadata,
)


def compute_traffic_dataframe_event_metadata(dataframe):
    return [
        EventMetadataEntry.text(
            str(min(dataframe["peak_traffic_load"])), "min_traffic_load", "Best Peak Load"
        ),
        EventMetadataEntry.text(
            str(max(dataframe["peak_traffic_load"])), "max_traffic_load", "Worst Peak Load"
        ),
        EventMetadataEntry.text(
            str(mean(dataframe["peak_traffic_load"])),
            "mean_traffic_load",
            "Mean peak traffic",
        ),
        EventMetadataEntry.text(
            str(median(dataframe["peak_traffic_load"])),
            "median_traffic_load",
            "Median peak traffic",
        ),
        EventMetadataEntry.text(
            str(len(dataframe)), "n_rows", "Number of rows seen in the dataframe"
        ),
        EventMetadataEntry.text(
            str(dataframe.columns), "columns", "Keys of columns seen in the dataframe"
        ),
    ]


TrafficDataFrame = create_dagster_pandas_dataframe_type(
    name="TrafficDataFrame",
    columns=[
        PandasColumn.string_column("interval_date"),
        PandasColumn.integer_column("peak_traffic_load", min_value=0),
    ],
    event_metadata_fn=compute_traffic_dataframe_event_metadata,
)


def compute_weather_dataframe_event_metadata(dataframe):
    return [
        EventMetadataEntry.text(
            str(len(dataframe)), "n_rows", "Number of rows seen in the dataframe"
        ),
        EventMetadataEntry.text(
            str(dataframe.columns), "columns", "Keys of columns seen in the dataframe"
        ),
    ]


WeatherDataFrameSchema = [
    PandasColumn.datetime_column("time", unique=True),
    PandasColumn.string_column("summary"),
    PandasColumn.categorical_column(
        "icon", categories={"clear-day", "cloudy", "fog", "partly-cloudy-day", "rain"}
    ),
    PandasColumn.integer_column("sunriseTime", min_value=0),
    PandasColumn.integer_column("sunsetTime", min_value=0),
    PandasColumn.float_column("precipIntensity", min_value=0.0, max_value=1.0),
    PandasColumn.float_column("precipIntensityMax", min_value=0.0, max_value=1.0),
    PandasColumn.float_column("precipProbability", min_value=0.0, max_value=1.0),
    PandasColumn.float_column("temperatureHigh", min_value=40.0, max_value=100.0),
    PandasColumn.integer_column("temperatureHighTime", min_value=0),
    PandasColumn.float_column("temperatureLow", min_value=30.0, max_value=100.0),
    PandasColumn.integer_column("temperatureLowTime", min_value=0),
    PandasColumn.float_column("dewPoint", min_value=10.0, max_value=70.0),
    PandasColumn.float_column("humidity", min_value=0.0, max_value=1.0),
    PandasColumn.float_column("pressure", min_value=900.0, max_value=1200.0),
    PandasColumn.float_column("windSpeed", min_value=0.0, max_value=100.0),
    PandasColumn.float_column("windGust", min_value=0.0, max_value=40.0),
    PandasColumn.integer_column("windGustTime", min_value=0),
    PandasColumn.integer_column("windBearing", min_value=0),
    PandasColumn.float_column("cloudCover", min_value=0.0, max_value=1.0),
    PandasColumn.integer_column("uvIndex", min_value=0, max_value=12),
    PandasColumn.integer_column("uvIndexTime", min_value=0),
    PandasColumn.numeric_column("visibility", min_value=0.0, max_value=10.0),
    PandasColumn.float_column("ozone", min_value=200.0, max_value=500.0),
]


WeatherDataFrame = create_dagster_pandas_dataframe_type(
    name="WeatherDataFrame",
    columns=WeatherDataFrameSchema,
    event_metadata_fn=compute_weather_dataframe_event_metadata,
)


def validate_snapshot_timeseries(_, training_set_data):
    if not isinstance(training_set_data, tuple):
        return TypeCheck(False)

    if len(training_set_data) != 2:
        return TypeCheck(
            success=False,
            description="Invalid training set. The tuple must consist of a training set, output vector, and feature_names",
        )
    # tuple argument types
    X, y = training_set_data
    if not (isinstance(X, ndarray) and isinstance(y, ndarray)):
        return TypeCheck(
            success=False,
            description="Both input matrix and output vector must be numpy arrays. X: {} | y: {}".format(
                type(X), type(y)
            ),
        )

    timeseries_length, snapshot_length, num_timeseries = X.shape
    output_vector_length = y.shape[0]
    if num_timeseries == 0 or output_vector_length == 0:
        return TypeCheck(
            success=False,
            description="No empty training sets allowed",
        )

    if timeseries_length != output_vector_length:
        return TypeCheck(
            success=False, description="Every timeseries must have as many snapshots as outputs"
        )

    return TypeCheck(
        success=True,
        metadata_entries=[
            EventMetadataEntry.text(
                str(num_timeseries), "num_ts", "Number of parallel timeseries."
            ),
            EventMetadataEntry.text(
                str(timeseries_length), "timeseries_length", "Length of each timeseries."
            ),
            EventMetadataEntry.text(
                str(snapshot_length),
                "snapshot_length",
                "Number of past observations for each input.",
            ),
        ],
    )


TrainingSet = DagsterType(
    name="TrainingSet",
    description="Final training set ready for the ml pipeline",
    type_check_fn=validate_snapshot_timeseries,
)
