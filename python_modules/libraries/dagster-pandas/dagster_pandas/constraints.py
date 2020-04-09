from datetime import datetime

from pandas import DataFrame

from dagster import check


class ConstraintViolationException(Exception):
    '''Indicates that a constraint has been violated.'''


class DataFrameConstraintViolationException(ConstraintViolationException):
    '''Indicates a dataframe level constraint has been violated.'''

    def __init__(self, constraint_name, constraint_description):
        super(DataFrameConstraintViolationException, self).__init__(
            "Violated {constraint_name} - {constraint_description}".format(
                constraint_name=constraint_name, constraint_description=constraint_description
            )
        )


class ColumnConstraintViolationException(ConstraintViolationException):
    '''Indicates that a column constraint has been violated.'''

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
    '''
    Base constraint object that all constraints inherit from.

    Args:
        error_description (Optional[str]): The plain string description that is output in the terminal if the constraint fails.
        markdown_description (Optional[str]): A markdown supported description that is emitted by dagit if the constraint fails.
    '''

    def __init__(self, error_description=None, markdown_description=None):
        self.name = self.__class__.__name__
        self.markdown_description = check.str_param(markdown_description, 'markdown_description')
        self.error_description = check.str_param(error_description, 'error_description')


class DataFrameConstraint(Constraint):
    '''
    Base constraint object that represent Dataframe shape constraints.

    Args:
        error_description (Optional[str]): The plain string description that is output in the terminal if the constraint fails.
        markdown_description (Optional[str]): A markdown supported description that is emitted by dagit if the constraint fails.
    '''

    def __init__(self, error_description=None, markdown_description=None):
        super(DataFrameConstraint, self).__init__(
            error_description=error_description, markdown_description=markdown_description
        )

    def validate(self, dataframe):
        raise NotImplementedError()


class StrictColumnsConstraint(DataFrameConstraint):
    '''
    A dataframe constraint that validates column existence and ordering.

    Args:
        strict_column_list (List[str]): The exact list of columns that your dataframe must have.
        enforce_ordering (Optional[bool]): If true, will enforce that the ordering of column names must match.
            Default is False.
    '''

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
    '''
    A dataframe constraint that validates the expected count of rows.

    Args:
        num_allowed_rows (int): The number of allowed rows in your dataframe.
        error_tolerance (Optional[int]): The acceptable threshold if you are not completely certain. Defaults to 0.
    '''

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
    '''
    Base constraint object that represent dataframe column shape constraints.

    Args:
        error_description (Optional[str]): The plain string description that is output in the terminal if the constraint fails.
        markdown_description (Optional[str]): A markdown supported description that is emitted by dagit if the constraint fails.
    '''

    def __init__(self, error_description=None, markdown_description=None):
        super(ColumnConstraint, self).__init__(
            error_description=error_description, markdown_description=markdown_description
        )

    def validate(self, dataframe, column_name):
        pass

    @staticmethod
    def get_offending_row_pairs(dataframe, column_name):
        return zip(dataframe.index.tolist(), dataframe[column_name].tolist())


class ColumnDTypeFnConstraint(ColumnConstraint):
    '''
    A column constraint that applies a pandas dtype validation function to a columns dtypes.

    Args:
        type_fn (Callable[[Set[str]], bool]): This is a function that takes the pandas columns dtypes and
            returns if those dtypes match the types it expects. See pandas.core.dtypes.common for examples.
    '''

    def __init__(self, type_fn):
        self.type_fn = check.callable_param(type_fn, 'type_fn')
        description = "{fn} must evaluate to True for column dtypes".format(
            fn=self.type_fn.__name__
        )
        super(ColumnDTypeFnConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe, column_name):
        received_dtypes = dataframe[column_name].dtype
        if not self.type_fn(received_dtypes):
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description='{base_error_message}. Dtypes received: {received_dtypes}.'.format(
                    base_error_message=self.error_description, received_dtypes=received_dtypes
                ),
                column_name=column_name,
            )


class ColumnDTypeInSetConstraint(ColumnConstraint):
    '''
    A column constraint that validates the pandas column dtypes based on the expected set of dtypes.

    Args:
        expected_dtype_set (Set[str]): The set of pandas dtypes that the pandas column dtypes must match.
    '''

    def __init__(self, expected_dtype_set):
        self.expected_dtype_set = check.set_param(expected_dtype_set, 'expected_dtype_set')
        description = "Column dtype must be in the following set {}.".format(
            self.expected_dtype_set
        )
        super(ColumnDTypeInSetConstraint, self).__init__(
            error_description=description, markdown_description=description
        )

    def validate(self, dataframe, column_name):
        received_dtypes = dataframe[column_name].dtype
        if str(received_dtypes) not in self.expected_dtype_set:
            raise ColumnConstraintViolationException(
                constraint_name=self.name,
                constraint_description='{base_error_message}. DTypes received: {received_dtypes}'.format(
                    base_error_message=self.error_description, received_dtypes=received_dtypes
                ),
                column_name=column_name,
            )


class NonNullableColumnConstraint(ColumnConstraint):
    '''
    A column constraint that ensures all values in a pandas column are not null.
    '''

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
    '''
    A column constraint that ensures all values in a pandas column are unique.

    Args:
        ignore_missing_vals (bool): If true, this constraint will enforce the constraint on non missing values.
    '''

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
    '''
    A column constraint that ensures all values in a pandas column are a valid category.

    Args:
        categories (Set[str]): Set of categories that values in your pandas column must match.
        ignore_missing_vals (bool): If true, this constraint will enforce the constraint on non missing values.
    '''

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
    '''
    A column constraint that ensures all values in a pandas column are greater than the provided
    lower bound [inclusive].

    Args:
        min_value (Union[int, float, datetime.datetime]): The lower bound.
        ignore_missing_vals (bool): If true, this constraint will enforce the constraint on non missing values.
    '''

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
    '''
    A column constraint that ensures all values in a pandas column are less than the provided
    upper bound [inclusive].

    Args:
        max_value (Union[int, float, datetime.datetime]): The upper bound.
        ignore_missing_vals (bool): If true, this constraint will enforce the constraint on non missing values.
    '''

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
    '''
    A column constraint that ensures all values in a pandas column are between the lower and upper bound [inclusive].

    Args:
        min_value (Union[int, float, datetime.datetime]): The lower bound.
        max_value (Union[int, float, datetime.datetime]): The upper bound.
        ignore_missing_vals (bool): If true, this constraint will enforce the constraint on non missing values.
    '''

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
