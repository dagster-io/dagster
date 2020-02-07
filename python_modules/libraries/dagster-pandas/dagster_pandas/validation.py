from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    Constraint,
    DataFrameConstraint,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
    UniqueColumnConstraint,
)
from pandas import DataFrame, Timestamp

from dagster import check

PANDAS_NUMERIC_TYPES = {'int64', 'float'}


def _construct_keyword_constraints(non_nullable, unique):
    non_nullable = check.bool_param(non_nullable, 'exists')
    unique = check.bool_param(unique, 'unique')
    constraints = []
    if non_nullable:
        constraints.append(NonNullableColumnConstraint())
    if unique:
        constraints.append(UniqueColumnConstraint())
    return constraints


class PandasColumn:
    def __init__(self, name, constraints=None):
        self.name = check.str_param(name, 'name')
        self.constraints = [ColumnExistsConstraint()] + check.opt_list_param(
            constraints, 'constraints', of_type=Constraint
        )

    def validate(self, dataframe):
        for constraint in self.constraints:
            constraint.validate(dataframe, self.name)

    @staticmethod
    def exists(name, non_nullable=False, unique=False):
        return PandasColumn(
            name=check.str_param(name, 'name'),
            constraints=_construct_keyword_constraints(non_nullable=non_nullable, unique=unique),
        )

    @staticmethod
    def boolean_column(name, non_nullable=False, unique=False):
        return PandasColumn(
            name=check.str_param(name, 'name'),
            constraints=[ColumnTypeConstraint('bool')]
            + _construct_keyword_constraints(non_nullable=non_nullable, unique=unique),
        )

    @staticmethod
    def numeric_column(
        name,
        expected_dtypes,
        min_value=-float('inf'),
        max_value=float('inf'),
        non_nullable=False,
        unique=False,
    ):
        return PandasColumn(
            name=check.str_param(name, 'name'),
            constraints=[
                ColumnTypeConstraint(expected_dtypes),
                InRangeColumnConstraint(
                    check.numeric_param(min_value, 'min_value'),
                    check.numeric_param(max_value, 'max_value'),
                ),
            ]
            + _construct_keyword_constraints(non_nullable=non_nullable, unique=unique),
        )

    @staticmethod
    def integer_column(
        name, min_value=-float('inf'), max_value=float('inf'), non_nullable=False, unique=False
    ):
        return PandasColumn.numeric_column(
            name, 'int64', min_value, max_value, non_nullable=non_nullable, unique=unique
        )

    @staticmethod
    def float_column(
        name, min_value=-float('inf'), max_value=float('inf'), non_nullable=False, unique=False
    ):
        return PandasColumn.numeric_column(
            name, 'float64', min_value, max_value, non_nullable=non_nullable, unique=unique
        )

    @staticmethod
    def datetime_column(
        name,
        min_datetime=Timestamp.min,
        max_datetime=Timestamp.max,
        non_nullable=False,
        unique=False,
    ):
        return PandasColumn(
            name=check.str_param(name, 'name'),
            constraints=[
                ColumnTypeConstraint({'datetime64[ns]'}),
                InRangeColumnConstraint(min_datetime, max_datetime),
            ]
            + _construct_keyword_constraints(non_nullable=non_nullable, unique=unique),
        )

    @staticmethod
    def string_column(name, non_nullable=False, unique=False):
        return PandasColumn(
            name=check.str_param(name, 'name'),
            constraints=[ColumnTypeConstraint('object')]
            + _construct_keyword_constraints(non_nullable=non_nullable, unique=unique),
        )

    @staticmethod
    def categorical_column(name, categories, of_types='object', non_nullable=False, unique=False):
        return PandasColumn(
            name=check.str_param(name, 'name'),
            constraints=[ColumnTypeConstraint(of_types), CategoricalColumnConstraint(categories)]
            + _construct_keyword_constraints(non_nullable=non_nullable, unique=unique),
        )


def validate_constraints(dataframe, pandas_columns=None, dataframe_constraints=None):
    dataframe = check.inst_param(dataframe, 'dataframe', DataFrame)
    pandas_columns = check.opt_list_param(
        pandas_columns, 'column_constraints', of_type=PandasColumn
    )
    dataframe_constraints = check.opt_list_param(
        dataframe_constraints, 'dataframe_constraints', of_type=DataFrameConstraint
    )

    if pandas_columns:
        for column in pandas_columns:
            column.validate(dataframe)

    if dataframe_constraints:
        for dataframe_constraint in dataframe_constraints:
            dataframe_constraint.validate(dataframe)
