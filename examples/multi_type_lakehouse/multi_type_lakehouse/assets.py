'''Asset definitions for the multi_type_lakehouse example.'''
import pandas as pd
from lakehouse import Column, computed_table, source_table
from pandas import DataFrame as PandasDF
from pyarrow import date32, float64, string
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import Window
from pyspark.sql import functions as f

sfo_q2_weather_sample_table = source_table(
    storage_key='filesystem',
    path=('sfo_q2_weather_sample',),
    columns=[Column('tmpf', float64()), Column('valid_date', string())],
)


@computed_table(
    storage_key='filesystem',
    input_assets=[sfo_q2_weather_sample_table],
    columns=[Column('valid_date', date32()), Column('max_tmpf', float64())],
)
def daily_temperature_highs_table(sfo_q2_weather_sample: PandasDF) -> PandasDF:
    '''Computes the temperature high for each day'''
    sfo_q2_weather_sample['valid_date'] = pd.to_datetime(sfo_q2_weather_sample['valid'])
    return sfo_q2_weather_sample.groupby('valid_date').max().rename(columns={'tmpf': 'max_tmpf'})


@computed_table(
    storage_key='filesystem',
    input_assets=[daily_temperature_highs_table],
    columns=[Column('valid_date', date32()), Column('max_tmpf', float64())],
)
def daily_temperature_high_diffs_table(daily_temperature_highs: SparkDF) -> SparkDF:
    '''Computes the difference between each day's high and the previous day's high'''
    window = Window.orderBy('valid_date')
    return daily_temperature_highs.select(
        'valid_date',
        (
            daily_temperature_highs['max_tmpf']
            - f.lag(daily_temperature_highs['max_tmpf']).over(window)
        ).alias('day_high_diff'),
    )
