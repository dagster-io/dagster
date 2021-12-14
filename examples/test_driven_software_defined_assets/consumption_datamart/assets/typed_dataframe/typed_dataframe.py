import decimal

import numpy
import pandas
from sqlalchemy import Column, String, Date, DateTime, Boolean, Integer, Float, Numeric
from sqlalchemy.ext.mutable import MutableList

from dagster import EventMetadata
from dagster_pandas import PandasColumn
from dagster_pandas import create_dagster_pandas_dataframe_type


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


def make_typed_dataframe_dagster_type(name, schema, dataframe_constraints=None, dataframe_loader=None):
    columns = []

    # Extract all fields of type Column in the (child) class
    for field_name, field_value in schema.__dict__.items():
        if isinstance(field_value, Column):
            columns.append(field_value)

    # Add standard columns
    columns.append(Column('meta__warnings', String, nullable=True, comment="Semi-colon seperated list of data warnings detected in this rows data"))

    def _extract_event_metadata(df: pandas.DataFrame):
        warning_count = 0
        if len(df.meta__warnings.dropna()) > 0:
            warning_count = len(df.meta__warnings.dropna().str.split(";").sum())
        return {
            "Row count": EventMetadata.int(len(df)),
            "Schema": EventMetadata.md(pandas.DataFrame({
                "Column": [column.name for column in columns],
                "Type": [column.type for column in columns],
                "Description": [column.description for column in columns]
            }).to_markdown(index=False)),
            "Warnings": warning_count,
            "Tail(5)": EventMetadata.md(df.tail(5).to_markdown()),
        }

    def _convert_dtypes(df_orig):
        df = df_orig.copy()
        for column in columns:
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

    data_frame_type = create_dagster_pandas_dataframe_type(
        name=name,
        columns=[_make_pandas_column_from_sqlalchemy_column(column) for column in columns],
        loader=dataframe_loader,
        dataframe_constraints=dataframe_constraints
    )

    data_frame_type.convert_dtypes = _convert_dtypes
    data_frame_type.extract_event_metadata = _extract_event_metadata
    data_frame_type.empty = _empty

    return data_frame_type
