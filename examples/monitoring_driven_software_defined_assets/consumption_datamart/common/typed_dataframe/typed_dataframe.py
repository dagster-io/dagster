import decimal

import numpy
import pandas
from sqlalchemy import Column, String, Date, DateTime, Boolean, Integer, Float, Numeric
from sqlalchemy.ext.mutable import MutableList

from dagster import EventMetadata, check
from dagster_pandas import PandasColumn
from dagster_pandas import create_dagster_pandas_dataframe_type
from dagster_pandas.constraints import DataFrameConstraint


def _make_pandas_column_from_sqlalchemy_column(
        column: Column,
        nullable=None,
        categories=None,
        min_value=-float("inf"),
        max_value=float("inf"),
        extra_constraints=[]
) -> PandasColumn:
    """
    :param column: SQLAlchemy Column definition
    :param nullable: optional - Override column.nullable
    :param min_value: optional - The lower bound for values you expect in this column. Defaults to -float('inf')
    :param max_value: optional - The upper bound for values you expect in this column. Defaults to float('inf')
    :param categories: optional - Valid options for categorical columns
    :param extra_constraints: optional - List of additional ColumnConstraints
    :return: equivalent dagster_pandas.PandasColumn
    """

    non_nullable = not column.nullable
    if nullable:
        non_nullable = not nullable

    if categories:
        pandas_column = PandasColumn.categorical_column(
            column.name,
            non_nullable=non_nullable,
            categories=categories
        )
    elif isinstance(column.type, String):
        pandas_column = PandasColumn.string_column(
            column.name,
            non_nullable=non_nullable,
            ignore_missing_vals=column.nullable
        )
    elif isinstance(column.type, Date) or isinstance(column.type, DateTime):
        pandas_column = PandasColumn.datetime_column(
            column.name,
            non_nullable=non_nullable,
            ignore_missing_vals=column.nullable,
            tz='UTC'
        )
    elif isinstance(column.type, Boolean):
        pandas_column = PandasColumn.boolean_column(
            column.name,
            non_nullable=non_nullable,
            ignore_missing_vals=column.nullable
        )
    elif isinstance(column.type, Integer):
        pandas_column = PandasColumn.integer_column(
            column.name,
            non_nullable=non_nullable,
            ignore_missing_vals=column.nullable,
            min_value=min_value,
            max_value=max_value
        )
    elif isinstance(column.type, Float):
        pandas_column = PandasColumn.float_column(
            column.name,
            non_nullable=non_nullable,
            ignore_missing_vals=column.nullable,
            min_value=min_value,
            max_value=max_value
        )
    elif isinstance(column.type, Numeric):
        pandas_column = PandasColumn.decimal_column(
            column.name,
            non_nullable=non_nullable,
            ignore_missing_vals=column.nullable,
            min_value=min_value,
            max_value=max_value
        )
    else:
        raise NotImplementedError(f"Conversion for column type: {column.type} not implemented yet")

    if len(extra_constraints) > 0:
        pandas_column.constraints.extend(extra_constraints)

    return pandas_column


class DataFrameQualityConstraint(DataFrameConstraint):
    def __init__(self, schema):
        self.schema = schema
        description = f"Calculate a quality score for the dataframe of type {self.schema}"
        super(DataFrameQualityConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, df):
        check.inst_param(df, "dataframe", pandas.DataFrame)
        self.schema.calculate_data_quality(df)


def make_typed_dataframe_dagster_type(name, schema, dataframe_constraints=None, dataframe_loader=None):
    if dataframe_constraints is None:
        dataframe_constraints = []

    columns = schema.get_columns()

    def _extract_event_metadata(df: pandas.DataFrame):
        warning_count = 0
        if len(df.meta__warnings.dropna()) > 0:
            warning_count = len(df.meta__warnings.dropna().str.split(";").sum())
        return {
            "Row count": EventMetadata.int(len(df)),
            "Warnings": warning_count,
            "Tail(5)": EventMetadata.md(df.tail(5).to_markdown()),
        }

    def _schema_as_markdown():
        return pandas.DataFrame({
            "Column": [column.name for column in columns],
            "Type": [column.type for column in columns],
            "Description": [column.description for column in columns]
        }).to_markdown(index=False)

    def _convert_dtypes(df_orig):
        df = df_orig.copy()
        for column in columns:
            if column.name not in df.columns:
                df[column.name] = numpy.NaN
            if isinstance(column.type, String):
                objects_with_NaN = df[column.name].fillna(numpy.NaN)
                strings_with_nan = objects_with_NaN.astype(str)
                strings_with_numpy_NaN = strings_with_nan.replace('nan', numpy.NaN).replace('NaN', numpy.NaN)
                strings_even_if_only_have_numpy_NaN = strings_with_numpy_NaN.astype(object)
                df.loc[:, column.name] = strings_even_if_only_have_numpy_NaN
            elif isinstance(column.type, Date) or isinstance(column.type, DateTime):
                df.loc[:, column.name] = pandas.to_datetime(df[column.name], utc=True)
            elif isinstance(column.type, Integer):
                df.loc[:, column.name] = df[column.name].astype(int)
            elif isinstance(column.type, Float):
                df.loc[:, column.name] = df[column.name].astype(float)
            elif isinstance(column.type, Numeric):
                df.loc[:, column.name] = df[column.name].apply(decimal.Decimal)
            elif isinstance(column.type, Boolean):
                df.loc[:, column.name] = df[column.name].astype(bool)
            else:
                raise NotImplementedError(f"Type normalisation for column: {column.name} of type: {column.type} not implemented yet")
        return df

    def _empty():
        column_names = [column.name for column in columns]
        return _convert_dtypes(pandas.DataFrame(columns=column_names))

    def _calculate_data_quality(df):
        return schema.calculate_data_quality(df)

    data_frame_type = create_dagster_pandas_dataframe_type(
        name=name,
        columns=[_make_pandas_column_from_sqlalchemy_column(column) for column in columns],
        loader=dataframe_loader,
        dataframe_constraints=dataframe_constraints
    )

    data_frame_type.calculate_data_quality = _calculate_data_quality
    data_frame_type.convert_dtypes = _convert_dtypes
    data_frame_type.extract_event_metadata = _extract_event_metadata
    data_frame_type.schema_as_markdown = _schema_as_markdown
    data_frame_type.empty = _empty

    return data_frame_type


def list_to_str(values: list):
    s = ';'.join(str(v) for v in values if pandas.notna(v))
    return s


def str_to_list(values: str):
    if pandas.isna(values):
        return []
    return values.split(';')
