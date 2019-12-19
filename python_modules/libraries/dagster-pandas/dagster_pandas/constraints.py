from abc import ABCMeta, abstractmethod

from pandas import DataFrame
from six import with_metaclass

from dagster import check


class ConstraintViolationException(Exception):
    def __init__(self, constraint_name, constraint_description, column_name, offending_rows=None):
        self.constraint_name = constraint_name
        self.constraint_description = constraint_description
        self.column_name = column_name
        self.offending_rows = offending_rows
        super(ConstraintViolationException, self).__init__(self.construct_message())

    def construct_message(self):
        base_message = "Violated {constraint_name} ({constraint_description}) for Column Name ({column_name}) ".format(
            constraint_name=self.constraint_name,
            constraint_description=self.constraint_description,
            column_name=self.column_name,
        )
        if self.offending_rows is not None:
            base_message += "The offending (index, row values) are the following: {}".format(
                self.offending_rows
            )
        return base_message


class Constraint(with_metaclass(ABCMeta)):
    def __init__(self, description=None):
        self.name = self.__class__.__name__
        self.description = check.str_param(description, 'description')

    @abstractmethod
    def validate(self, dataframe, column_name):
        pass

    @staticmethod
    def get_offending_row_pairs(dataframe, column_name):
        return zip(dataframe.index.tolist(), dataframe[column_name].tolist())


class ColumnExistsConstraint(Constraint):
    def __init__(self):
        super(ColumnExistsConstraint, self).__init__("Column Name must exist in dataframe")

    def validate(self, dataframe, column_name):
        check.inst_param(dataframe, 'dataframe', DataFrame)
        check.str_param(column_name, 'column_name')

        if column_name not in dataframe.columns:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
            )


class ColumnTypeConstraint(Constraint):
    def __init__(self, expected_pandas_dtypes):
        if isinstance(expected_pandas_dtypes, str):
            expected_pandas_dtypes = {expected_pandas_dtypes}
        self.expected_pandas_dtypes = check.set_param(
            expected_pandas_dtypes, 'expected_pandas_dtype'
        )
        super(ColumnTypeConstraint, self).__init__(
            "Column dtype must be {}".format(self.expected_pandas_dtypes)
        )

    def validate(self, dataframe, column_name):
        if str(dataframe[column_name].dtype) not in self.expected_pandas_dtypes:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
            )


class NonNullableColumnConstraint(Constraint):
    def __init__(self):
        super(NonNullableColumnConstraint, self).__init__("Column must contain non null values")

    def validate(self, dataframe, column_name):
        rows_with_null_columns = dataframe[dataframe[column_name].isna()]
        if not rows_with_null_columns.empty:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
                offending_rows=self.get_offending_row_pairs(rows_with_null_columns, column_name),
            )


class UniqueColumnConstraint(Constraint):
    def __init__(self):
        super(UniqueColumnConstraint, self).__init__("Column must contain unique values")

    def validate(self, dataframe, column_name):
        rows_with_duplicated_values = dataframe[dataframe[column_name].duplicated()]
        if not rows_with_duplicated_values.empty:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
                offending_rows=rows_with_duplicated_values,
            )


class CategoricalColumnConstraint(Constraint):
    def __init__(self, categories):
        self.categories = check.set_param(categories, 'categories', of_type=str)
        super(CategoricalColumnConstraint, self).__init__(
            "Column must take the following values {}".format(self.categories)
        )

    def validate(self, dataframe, column_name):
        rows_with_unexpected_buckets = dataframe[~dataframe[column_name].isin(self.categories)]
        if not rows_with_unexpected_buckets.empty:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
                offending_rows=rows_with_unexpected_buckets,
            )


class MinValueColumnConstraint(Constraint):
    def __init__(self, min_value):
        self.min_value = min_value
        super(MinValueColumnConstraint, self).__init__(
            "Column must have values greater than {}".format(self.min_value)
        )

    def validate(self, dataframe, column_name):
        out_of_bounds_rows = dataframe[dataframe[column_name] < self.min_value]
        if not out_of_bounds_rows.empty:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
                offending_rows=out_of_bounds_rows,
            )


class MaxValueColumnConstraint(Constraint):
    def __init__(self, max_value):
        self.max_value = max_value
        super(MaxValueColumnConstraint, self).__init__(
            "Column must have values greater than {}".format(self.max_value)
        )

    def validate(self, dataframe, column_name):
        out_of_bounds_rows = dataframe[dataframe[column_name] > self.max_value]
        if not out_of_bounds_rows.empty:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
                offending_rows=out_of_bounds_rows,
            )


class InRangeColumnConstraint(Constraint):
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value
        super(InRangeColumnConstraint, self).__init__(
            "Column must have values between {} and {}".format(self.min_value, self.max_value)
        )

    def validate(self, dataframe, column_name):
        out_of_bounds_rows = dataframe[
            ~dataframe[column_name].between(self.min_value, self.max_value)
        ]
        if not out_of_bounds_rows.empty:
            raise ConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.description,
                column_name=column_name,
                offending_rows=out_of_bounds_rows,
            )
