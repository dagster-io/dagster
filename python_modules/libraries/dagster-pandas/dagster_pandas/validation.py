from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    Constraint,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
)
from pandas import DataFrame, Timestamp

from dagster import check

_BASE_CONSTRAINTS = [
    ColumnExistsConstraint(),
]

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
    def resolve_nullable_constraints(constraints, nullable):
        if not nullable:
            constraints.append(NonNullableColumnConstraint())
        return constraints

    @classmethod
    def numeric_column(
        cls, name, expected_dtypes, min_value=-float('inf'), max_value=float('inf'), nullable=True
    ):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.resolve_nullable_constraints(
                [
                    ColumnTypeConstraint(expected_dtypes),
                    InRangeColumnConstraint(
                        check.numeric_param(min_value, 'min_value'),
                        check.numeric_param(max_value, 'max_value'),
                    ),
                ],
                nullable,
            ),
        )

    @classmethod
    def integer_column(cls, name, min_value=-float('inf'), max_value=float('inf'), nullable=True):
        return cls.numeric_column(name, 'int64', min_value, max_value, nullable)

    @classmethod
    def float_column(cls, name, min_value=-float('inf'), max_value=float('inf'), nullable=True):
        return cls.numeric_column(name, 'float', min_value, max_value, nullable)

    @classmethod
    def datetime_column(
        cls, name, min_datetime=Timestamp.min, max_datetime=Timestamp.max, nullable=True
    ):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.resolve_nullable_constraints(
                [
                    ColumnTypeConstraint({'datetime64[ns]'}),
                    InRangeColumnConstraint(min_datetime, max_datetime),
                ],
                nullable,
            ),
        )

    @classmethod
    def string_column(cls, name, nullable=True):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.resolve_nullable_constraints(
                [ColumnTypeConstraint('object')], nullable
            ),
        )

    @classmethod
    def categorical_column(cls, name, categories, of_types='object', nullable=True):
        return cls(
            name=check.str_param(name, 'name'),
            constraints=cls.resolve_nullable_constraints(
                [ColumnTypeConstraint(of_types), CategoricalColumnConstraint(categories),], nullable
            ),
        )


def validate_collection_schema(collection_schema, dataframe):
    collection_schema = check.list_param(
        collection_schema, 'collection_schema', of_type=PandasColumn
    )
    dataframe = check.inst_param(dataframe, 'dataframe', DataFrame)

    for column in collection_schema:
        column.validate(dataframe)
