from decimal import Decimal

from dagster import check
from dagster_pandas import PandasColumn
from dagster_pandas.constraints import ColumnConstraint, ColumnConstraintViolationException, InRangeColumnConstraint
from dagster_pandas.validation import _construct_keyword_constraints


class NoDuplicatesConstraint(ColumnConstraint):
    def __init__(self):
        message = "Cannot have duplicate values "
        super(NoDuplicatesConstraint, self).__init__(
            error_description=message, markdown_description=message
        )

    def validate(self, dataframe, column_name):
        df_without_na = dataframe.dropna(subset=[column_name])
        rows_with_duplicates = df_without_na[df_without_na.duplicated([column_name])]
        if not rows_with_duplicates.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=rows_with_duplicates,
            )


class ColumnContainsDecimalsConstraint(ColumnConstraint):
    """
    A column constraint that ensures the column only contains Decimal values.
    """

    def __init__(self):
        description = f'Column can only contain Decimal values'
        super(ColumnContainsDecimalsConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe, column_name):
        for v in dataframe[column_name]:
            if not isinstance(v, Decimal):
                raise ColumnConstraintViolationException(
                    constraint_name=self.name,
                    constraint_description=f'{self.error_description}, but contained "{v}"',
                    column_name=column_name,
                )


def decimal_column(
        name,
        min_value=Decimal('-Infinity'),
        max_value=Decimal('Infinity'),
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False,
        is_required=None,
):
    """
    Simple constructor for PandasColumns that expresses decimal constraints numeric dtypes.

    Args:
        name (str): Name of the column. This must match up with the column name in the dataframe you
            expect to receive.
        min_value (Optional[Union[int,Decimal]]): The lower bound for values you expect in this column. Defaults to Decimal('-Infinity')
        max_value (Optional[Union[int,Decimal]]): The upper bound for values you expect in this column. Defaults to Decimal('Infinity')
        non_nullable (Optional[bool]): If true, this column will enforce a constraint that all values in the column
            ought to be non null values.
        unique (Optional[bool]): If true, this column will enforce a uniqueness constraint on the column values.
        ignore_missing_vals (Optional[bool]): A flag that is passed into most constraints. If true, the constraint will
            only evaluate non-null data. Ignore_missing_vals and non_nullable cannot both be True.
        is_required (Optional[bool]): Flag indicating the optional/required presence of the column.
            If the column exists the validate function will validate the column. Default to True.
    """

    return PandasColumn(
        name=check.str_param(name, "name"),
        constraints=[
                        ColumnContainsDecimalsConstraint(),
                        InRangeColumnConstraint(
                            check.numeric_param(min_value, "min_value"),
                            check.numeric_param(max_value, "max_value"),
                            ignore_missing_vals=ignore_missing_vals,
                        ),
                    ]
                    + _construct_keyword_constraints(
            non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
        ),
        is_required=is_required,
    )
