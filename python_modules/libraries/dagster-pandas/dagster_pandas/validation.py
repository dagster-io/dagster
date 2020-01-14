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

_BASE_CONSTRAINTS = [
    ColumnExistsConstraint(),
]

_CONFIGURABLE_CONSTRAINTS = {
    'exists': NonNullableColumnConstraint,
    'unique': UniqueColumnConstraint,
}


PANDAS_NUMERIC_TYPES = {'int64', 'float'}


class PandasColumn:
    def __init__(self, name, constraints=None):
        self.name = check.str_param(name, 'name')
        self.constraints = _BASE_CONSTRAINTS + check.opt_list_param(
            constraints, 'constraints', of_type=Constraint
        )

    def validate(self, dataframe):
        for constraint in self.constraints:
            constraint.validate(dataframe, self.name)

    @staticmethod
    def add_configurable_constraints(constraints, **kwargs):
        for configurable_constraint_flag, constraint in _CONFIGURABLE_CONSTRAINTS.items():
            apply_constraint = kwargs.get(configurable_constraint_flag, False)
            if apply_constraint:
                constraints.append(constraint())
        return constraints

    @classmethod
    def boolean_column(cls, name, exists=False, unique=False):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.add_configurable_constraints(
                [ColumnTypeConstraint('bool')], exists=exists, unique=unique,
            ),
        )

    @classmethod
    def numeric_column(
        cls,
        name,
        expected_dtypes,
        min_value=-float('inf'),
        max_value=float('inf'),
        exists=False,
        unique=False,
    ):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.add_configurable_constraints(
                [
                    ColumnTypeConstraint(expected_dtypes),
                    InRangeColumnConstraint(
                        check.numeric_param(min_value, 'min_value'),
                        check.numeric_param(max_value, 'max_value'),
                    ),
                ],
                exists=exists,
                unique=unique,
            ),
        )

    @classmethod
    def integer_column(
        cls, name, min_value=-float('inf'), max_value=float('inf'), exists=False, unique=False
    ):
        return cls.numeric_column(name, 'int64', min_value, max_value, exists=exists, unique=unique)

    @classmethod
    def float_column(
        cls, name, min_value=-float('inf'), max_value=float('inf'), exists=False, unique=False
    ):
        return cls.numeric_column(
            name, 'float64', min_value, max_value, exists=exists, unique=unique
        )

    @classmethod
    def datetime_column(
        cls,
        name,
        min_datetime=Timestamp.min,
        max_datetime=Timestamp.max,
        exists=False,
        unique=False,
    ):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.add_configurable_constraints(
                [
                    ColumnTypeConstraint({'datetime64[ns]'}),
                    InRangeColumnConstraint(min_datetime, max_datetime),
                ],
                exists=exists,
                unique=unique,
            ),
        )

    @classmethod
    def string_column(cls, name, exists=False, unique=False):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.add_configurable_constraints(
                [ColumnTypeConstraint('object')], exists=exists, unique=unique
            ),
        )

    @classmethod
    def categorical_column(cls, name, categories, of_types='object', exists=False, unique=False):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.add_configurable_constraints(
                [ColumnTypeConstraint(of_types), CategoricalColumnConstraint(categories)],
                exists=exists,
                unique=unique,
            ),
        )


def validate_collection_schema(collection_schema, dataframe, dataframe_constraints=None):
    collection_schema = check.list_param(
        collection_schema, 'collection_schema', of_type=PandasColumn
    )
    dataframe = check.inst_param(dataframe, 'dataframe', DataFrame)
    dataframe_constraints = check.opt_list_param(
        dataframe_constraints, 'dataframe_constraints', of_type=DataFrameConstraint
    )

    for column in collection_schema:
        column.validate(dataframe)

    if dataframe_constraints:
        for dataframe_constraint in dataframe_constraints:
            dataframe_constraint.validate(dataframe)
