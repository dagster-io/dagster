from datetime import datetime

from pandas import DataFrame

from dagster import check


class ConstraintViolationException(Exception):
    pass


class DataFrameConstraintViolationException(ConstraintViolationException):
    def __init__(self, constraint_name, constraint_description):
        super(DataFrameConstraintViolationException, self).__init__(
            "Violated {constraint_name} - {constraint_description}".format(
                constraint_name=constraint_name, constraint_description=constraint_description
            )
        )


class ColumnConstraintViolationException(ConstraintViolationException):
    def __init__(self, constraint_name, constraint_description, column_name, offending_rows=None):
        self.constraint_name = constraint_name
        self.constraint_description = constraint_description
        self.column_name = column_name
        self.offending_rows = offending_rows
        super(ColumnConstraintViolationException, self).__init__(self.construct_message())

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


class Constraint(object):
    def __init__(self, error_description=None, markdown_description=None):
        self.name = self.__class__.__name__
        self.markdown_description = check.str_param(markdown_description, 'markdown_description')
        self.error_description = check.str_param(error_description, 'error_description')


class DataFrameConstraint(Constraint):
    def __init__(self, error_description=None, markdown_description=None):
        super(DataFrameConstraint, self).__init__(
            error_description=error_description, markdown_description=markdown_description
        )

    def validate(self, dataframe):
        raise NotImplementedError()


class StrictColumnsConstraint(DataFrameConstraint):
    def __init__(self, strict_column_list, enforce_ordering=False):
        self.enforce_ordering = check.bool_param(enforce_ordering, 'enforce_ordering')
        self.strict_column_list = check.list_param(
            strict_column_list, 'strict_column_list', of_type=str
        )
        description = "No columns outside of {cols} allowed. ".format(cols=self.strict_column_list)
        if enforce_ordering:
            description += "Columns must be in that order."
        super(StrictColumnsConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe):
        check.inst_param(dataframe, 'dataframe', DataFrame)
        columns_received = list(dataframe.columns)
        if self.enforce_ordering:
            if self.strict_column_list != columns_received:
                raise DataFrameConstraintViolationException(
                    constraint_name=self.name,
                    constraint_description="Expected the following ordering of columns {expected}. Received: {received}".format(
                        expected=self.strict_column_list, received=columns_received
                    ),
                )
        for column in columns_received:
            if column not in self.strict_column_list:
                raise DataFrameConstraintViolationException(
                    constraint_name=self.name,
                    constraint_description="Expected {}. Recevied {}.".format(
                        self.strict_column_list, columns_received
                    ),
                )


class RowCountConstraint(DataFrameConstraint):
    def __init__(self, num_allowed_rows, error_tolerance=0):
        self.num_allowed_rows = check.int_param(num_allowed_rows, "num_allowed_rows")
        self.error_tolerance = abs(check.int_param(error_tolerance, "error_tolerance"))
        if self.error_tolerance > self.num_allowed_rows:
            raise ValueError("Tolerance can't be greater than the number of rows you expect.")
        description = "Dataframe must have {} +- {} rows.".format(
            self.num_allowed_rows, self.error_tolerance
        )
        super(RowCountConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe):
        check.inst_param(dataframe, 'dataframe', DataFrame)

        if not (
            self.num_allowed_rows - self.error_tolerance
            <= len(dataframe)
            <= self.num_allowed_rows + self.error_tolerance
        ):
            raise DataFrameConstraintViolationException(
                constraint_name=self.name,
                constraint_description="Expected {expected} +- {tolerance} rows. Got {received}".format(
                    expected=self.num_allowed_rows,
                    tolerance=self.error_tolerance,
                    received=len(dataframe),
                ),
            )


def apply_ignore_missing_data_to_mask(mask, column):
    return mask & ~column.isnull()


class ColumnConstraint(Constraint):
    def __init__(self, error_description=None, markdown_description=None):
        super(ColumnConstraint, self).__init__(
            error_description=error_description, markdown_description=markdown_description
        )

    def validate(self, dataframe, column_name):
        pass

    @staticmethod
    def get_offending_row_pairs(dataframe, column_name):
        return zip(dataframe.index.tolist(), dataframe[column_name].tolist())


class ColumnTypeConstraint(ColumnConstraint):
    def __init__(self, expected_pandas_dtypes):
        if isinstance(expected_pandas_dtypes, str):
            expected_pandas_dtypes = {expected_pandas_dtypes}
        self.expected_pandas_dtypes = check.set_param(
            expected_pandas_dtypes, 'expected_pandas_dtype'
        )
        description = "Column dtype must be {}".format(self.expected_pandas_dtypes)
        super(ColumnTypeConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe, column_name):
        if str(dataframe[column_name].dtype) not in self.expected_pandas_dtypes:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
            )


class NonNullableColumnConstraint(ColumnConstraint):
    def __init__(self):
        description = "No Null values allowed."
        super(NonNullableColumnConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe, column_name):
        rows_with_null_columns = dataframe[dataframe[column_name].isna()]
        if not rows_with_null_columns.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=self.get_offending_row_pairs(rows_with_null_columns, column_name),
            )


class UniqueColumnConstraint(ColumnConstraint):
    def __init__(self, ignore_missing_vals):
        description = "Column must be unique."
        self.ignore_missing_vals = check.bool_param(ignore_missing_vals, 'ignore_missing_vals')
        super(UniqueColumnConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe, column_name):
        invalid = dataframe[column_name].duplicated()
        if self.ignore_missing_vals:
            invalid = apply_ignore_missing_data_to_mask(invalid, dataframe[column_name])
        rows_with_duplicated_values = dataframe[invalid]
        if not rows_with_duplicated_values.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=rows_with_duplicated_values,
            )


class CategoricalColumnConstraint(ColumnConstraint):
    def __init__(self, categories, ignore_missing_vals):
        self.categories = list(check.set_param(categories, 'categories', of_type=str))
        self.ignore_missing_vals = check.bool_param(ignore_missing_vals, 'ignore_missing_vals')
        super(CategoricalColumnConstraint, self).__init__(
            error_description="Expected Categories are {}".format(self.categories),
            markdown_description="Category examples are {}...".format(self.categories[:5]),
        )

    def validate(self, dataframe, column_name):
        invalid = ~dataframe[column_name].isin(self.categories)
        if self.ignore_missing_vals:
            invalid = apply_ignore_missing_data_to_mask(invalid, dataframe[column_name])
        rows_with_unexpected_buckets = dataframe[invalid]
        if not rows_with_unexpected_buckets.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=rows_with_unexpected_buckets,
            )


class MinValueColumnConstraint(ColumnConstraint):
    def __init__(self, min_value, ignore_missing_vals):
        self.min_value = check.inst_param(min_value, 'min_value', (int, float, datetime))
        self.ignore_missing_vals = check.bool_param(ignore_missing_vals, 'ignore_missing_vals')
        super(MinValueColumnConstraint, self).__init__(
            markdown_description="values > {}".format(self.min_value),
            error_description="Column must have values > {}".format(self.min_value),
        )

    def validate(self, dataframe, column_name):
        invalid = dataframe[column_name] < self.min_value
        if self.ignore_missing_vals:
            invalid = apply_ignore_missing_data_to_mask(invalid, dataframe[column_name])
        out_of_bounds_rows = dataframe[invalid]
        if not out_of_bounds_rows.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=out_of_bounds_rows,
            )


class MaxValueColumnConstraint(ColumnConstraint):
    def __init__(self, max_value, ignore_missing_vals):
        self.max_value = check.inst_param(max_value, 'max_value', (int, float, datetime))
        self.ignore_missing_vals = check.bool_param(ignore_missing_vals, 'ignore_missing_vals')
        super(MaxValueColumnConstraint, self).__init__(
            markdown_description="values < {}".format(self.max_value),
            error_description="Column must have values < {}".format(self.max_value),
        )

    def validate(self, dataframe, column_name):
        invalid = dataframe[column_name] > self.max_value
        if self.ignore_missing_vals:
            invalid = apply_ignore_missing_data_to_mask(invalid, dataframe[column_name])
        out_of_bounds_rows = dataframe[invalid]
        if not out_of_bounds_rows.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=out_of_bounds_rows,
            )


class InRangeColumnConstraint(ColumnConstraint):
    def __init__(self, min_value, max_value, ignore_missing_vals):
        self.min_value = check.inst_param(min_value, 'min_value', (int, float, datetime))
        self.max_value = check.inst_param(max_value, 'max_value', (int, float, datetime))
        self.ignore_missing_vals = check.bool_param(ignore_missing_vals, 'ignore_missing_vals')
        super(InRangeColumnConstraint, self).__init__(
            markdown_description="{} < values < {}".format(self.min_value, self.max_value),
            error_description="Column must have values between {} and {} inclusive.".format(
                self.min_value, self.max_value
            ),
        )

    def validate(self, dataframe, column_name):
        invalid = ~dataframe[column_name].between(self.min_value, self.max_value)
        if self.ignore_missing_vals:
            invalid = apply_ignore_missing_data_to_mask(invalid, dataframe[column_name])
        out_of_bounds_rows = dataframe[invalid]
        if not out_of_bounds_rows.empty:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description=self.error_description,
                column_name=column_name,
                offending_rows=out_of_bounds_rows,
            )
