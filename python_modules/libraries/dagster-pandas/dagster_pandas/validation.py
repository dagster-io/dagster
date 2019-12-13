from dagster_pandas.constraints import ColumnExistsConstraint, Constraint
from pandas import DataFrame

from dagster import check

BASE_CONSTRAINTS = [
    ColumnExistsConstraint(),
]


class PandasColumn:
    def __init__(self, name, constraints=None):
        self.name = check.str_param(name, 'name')
        self.constraints = BASE_CONSTRAINTS + check.opt_list_param(
            constraints, 'constraints', of_type=Constraint
        )

    def validate(self, dataframe):
        for constraint in self.constraints:
            constraint.validate(dataframe, self.name)


def validate_collection_schema(collection_schema, dataframe):
    collection_schema = check.list_param(
        collection_schema, 'collection_schema', of_type=PandasColumn
    )
    dataframe = check.inst_param(dataframe, 'dataframe', DataFrame)

    for column in collection_schema:
        column.validate(dataframe)
