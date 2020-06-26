import sys
from collections import defaultdict
from datetime import datetime

from pandas import DataFrame

from dagster import DagsterType, EventMetadataEntry, TypeCheck, check


class ConstraintViolationException(Exception):
    '''Indicates that a constraint has been violated.'''


class ConstraintWithMetadataException(Exception):
    """
    This class defines the response generated when a pandas DF fails validation -- it can be used to generate either a
    failed typecheck or an exception.

    Args:
        constraint_name (str):  the name of the violated constraint
        constraint_description (Optional[str]): the description of the violated constraint
        expectation (Optional[Union[dict,list, str, set]]): what result was expected -- typically a jsonlike, though it can be a string
        offending (Optional[Union[dict,list, str, set]]):  which pieces of the dataframe violated the expectation, typically list or string
        actual (Optional[Union[dict,list, str, set]]): what those pieces of the dataframe actually were -- typically a jsonlike
    """

    def __init__(
        self,
        constraint_name,
        constraint_description="",
        expectation=None,
        offending=None,
        actual=None,
    ):
        self.constraint_name = constraint_name
        self.constraint_description = constraint_description
        self.expectation = check.opt_inst_param(expectation, "expectation", (dict, list, str, set))
        self.offending = check.opt_inst_param(offending, "offending", (dict, list, str, set))
        self.actual = check.opt_inst_param(actual, "actual", (dict, list, str, set))
        super(ConstraintWithMetadataException, self).__init__(
            "Violated {} - {}, {} was/were expected, but we received {} which was/were {}".format(
                constraint_name, constraint_description, expectation, offending, actual,
            )
        )

    def convert_to_metadata(self):
        return EventMetadataEntry.json(
            {
                'constraint_name': self.constraint_name,
                'constraint_description': self.constraint_description,
                'expected': self.expectation,
                'offending': self.offending,
                'actual': self.actual,
            },
            'constraint-metadata',
        )

    def return_as_typecheck(self):
        return TypeCheck(
            success=False, description=self.args[0], metadata_entries=[self.convert_to_metadata()]
        )


class DataFrameConstraintViolationException(ConstraintViolationException):
    '''Indicates a dataframe level constraint has been violated.'''

    def __init__(self, constraint_name, constraint_description):
        super(DataFrameConstraintViolationException, self).__init__(
            "Violated {constraint_name} - {constraint_description}".format(
                constraint_name=constraint_name, constraint_description=constraint_description
            )
        )


class DataFrameWithMetadataException(ConstraintWithMetadataException):
    def __init__(self, constraint_name, constraint_description, expectation, actual):
        super(DataFrameWithMetadataException, self).__init__(
            constraint_name, constraint_description, expectation, 'a malformed dataframe', actual
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


class ColumnWithMetadataException(ConstraintWithMetadataException):
    def __init__(self, constraint_name, constraint_description, expectation, offending, actual):
        super(ColumnWithMetadataException, self).__init__(
            "the column constraint " + constraint_name,
            constraint_description,
            expectation,
            offending,
            actual,
        )


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


class ConstraintWithMetadata(object):
    """
    This class defines a base constraint over pandas DFs with organized metadata

    args:
        description (str): description of the constraint
        validation_fn (DataFrame -> Tuple[bool, dict[str, Union[dict,list, str, set]]]):  the validation function to run over inputted data
                    This function should return a tuple of a boolean for success or failure, and a dict containing
                    metadata about the test -- this metadata will be passed to the resulting exception if validation
                    fails.
        resulting_exception (ConstraintWithMetadataException):  what response a failed typecheck should induce
        raise_or_typecheck (Optional[bool]): whether to raise an exception (if set to True) or emit a failed typecheck event
                    (if set to False) when validation fails
        name (Optional[str]): what to call the constraint, defaults to the class name.
    """

    # TODO:  validation_fn returning metadata is sorta broken.  maybe have it yield typecheck events and grab metadata?

    def __init__(
        self, description, validation_fn, resulting_exception, raise_or_typecheck=True, name=None
    ):
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name
        self.description = description
        # should return a tuple of (bool, and either an empty dict or a dict of extra params)
        self.validation_fn = validation_fn
        self.resulting_exception = resulting_exception
        self.raise_or_typecheck = raise_or_typecheck

    def validate(self, data, *args, **kwargs):
        res = self.validation_fn(data, *args, **kwargs)
        if not res[0]:
            exc = self.resulting_exception(
                constraint_name=self.name, constraint_description=self.description, **res[1]
            )

            if self.raise_or_typecheck:
                raise exc
            else:
                return exc.return_as_typecheck()

        else:
            if res[0]:
                return TypeCheck(success=True)

    # TODO:  composition of validations
    def as_dagster_type(self, *args, **kwargs):
        if self.raise_or_typecheck:
            raise Exception(
                "Dagster types can only be constructed from constraints that return typechecks"
            )
        return DagsterType(
            name=self.name,
            description="A Pandas DataFrame with the following validation: {}".format(
                self.description
            ),
            type_check_fn=lambda x: self.validate(x, *args),
            **kwargs
        )


class MultiConstraintWithMetadata(ConstraintWithMetadata):
    """
        Use this class if you have multiple constraints to check over the entire dataframe

        args:
            description (str): description of the constraint
            validation_fn_arr(List[DataFrame -> Tuple[bool, dict[str, Any]]]):
                        a list of the validation functions to run over inputted data
                        Each function should return a tuple of a boolean for success or failure, and a dict containing
                        metadata about the test -- this metadata will be passed to the resulting exception if validation
                        fails.
            resulting_exception (ConstraintWithMetadataException):  what response a failed typecheck should induce
            raise_or_typecheck (Optional[bool]): whether to raise an exception (if set to True) or emit a failed typecheck event
                        (if set to False) when validation fails
            name (Optional[str]): what to call the constraint, defaults to the class name.
        """

    def __init__(
        self,
        description,
        validation_fn_arr,
        resulting_exception,
        raise_or_typecheck=True,
        name=None,
    ):
        validation_fn_arr = check.list_param(validation_fn_arr, "validation_fn_arr")

        def validation_fn(data, *args, **kwargs):

            results = [f(data, *args, **kwargs) for f in validation_fn_arr]
            truthparam = all(item[0] for item in results)
            metadict = defaultdict(dict)
            for i, dicta in enumerate(item[1] for item in results):
                if len(dicta.keys()) > 0:
                    for key in dicta:
                        metadict[key][validation_fn_arr[i].__name__] = dicta[key]
            return (truthparam, metadict)

        super(MultiConstraintWithMetadata, self).__init__(
            description,
            validation_fn,
            resulting_exception,
            raise_or_typecheck=raise_or_typecheck,
            name=name,
        )


class StrictColumnsWithMetadata(ConstraintWithMetadata):
    def __init__(self, column_list, enforce_ordering=False, raise_or_typecheck=True, name=None):
        self.enforce_ordering = check.bool_param(enforce_ordering, 'enforce_ordering')
        self.column_list = check.list_param(column_list, 'strict_column_list', of_type=str)

        def validation_fcn(inframe):
            if list(inframe.columns) == column_list:
                return (True, {})
            else:
                if self.enforce_ordering:
                    resdict = {'expectation': self.column_list, 'actual': list(inframe.columns)}
                    return (False, resdict)
                else:
                    if set(inframe.columns) == set(column_list):
                        return (True, {})
                    else:
                        extra = [x for x in inframe.columns if x not in set(column_list)]
                        missing = [x for x in set(column_list) if x not in inframe.columns]
                        resdict = {
                            'expectation': self.column_list,
                            'actual': {'extra_columns': extra, 'missing_columns': missing},
                        }
                        return (False, resdict)

        basestr = "ensuring that the right columns, {} were present".format(self.column_list)
        if enforce_ordering:
            basestr += " in the right order"
        super(StrictColumnsWithMetadata, self).__init__(
            basestr,
            validation_fcn,
            DataFrameWithMetadataException,
            raise_or_typecheck=raise_or_typecheck,
            name=name,
        )


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


class ColumnAggregateConstraintWithMetadata(ConstraintWithMetadata):
    def validate(self, data, *columns, **kwargs):
        if len(columns) == 0:
            columns = data.columns
        relevant_data = data[list(columns)]
        offending_columns = set()
        offending_values = {}
        for column in columns:
            # TODO: grab extra metadata
            if not self.validation_fn(relevant_data[column])[0]:
                offending_columns.add(column)
                offending_values[column] = relevant_data[column].to_numpy()
        if len(offending_columns) == 0 and not self.raise_or_typecheck:
            return TypeCheck(success=True)
        elif len(offending_columns) > 0:
            metadict = {
                'expectation': self.description.replace('Confirms', ''),
                'actual': offending_values,
                'offending': offending_columns,
            }
            exc = self.resulting_exception(
                constraint_name=self.name, constraint_description=self.description, **metadict
            )

            if self.raise_or_typecheck:
                raise exc
            else:
                return exc.return_as_typecheck()


class ColumnConstraintWithMetadata(ConstraintWithMetadata):
    """
    This class is useful for constructing single constraints that
    you want to apply to multiple columns of your dataframe
    """

    def validate(self, data, *columns, **kwargs):
        if len(columns) == 0:
            columns = data.columns
        relevant_data = data[list(columns)]
        offending = {}
        offending_values = {}
        # TODO:  grab metadata from here
        inverse_validation = lambda x: not self.validation_fn(x)[0]
        for column in columns:
            results = relevant_data[relevant_data[column].apply(inverse_validation)]
            if len(results.index.tolist()) > 0:
                offending[column] = ['row ' + str(i) for i in (results.index.tolist())]
                offending_values[column] = results[column].tolist()
        if len(offending) == 0:
            if not self.raise_or_typecheck:
                return TypeCheck(success=True)
        else:
            metadict = {
                'expectation': self.validation_fn.__doc__,
                'actual': offending_values,
                'offending': offending,
            }
            exc = self.resulting_exception(
                constraint_name=self.name, constraint_description=self.description, **metadict
            )

            if self.raise_or_typecheck:
                raise exc
            else:
                return exc.return_as_typecheck()


class MultiColumnConstraintWithMetadata(ColumnConstraintWithMetadata):
    """
        This class is useful for constructing more complicated relationships between columns
        and expectations -- i.e. you want some validations on column A, others on column B, etc.
        This lets you package up the metadata neatly,
        and also allows for cases like 'fail if any one of these constraints fails but still run all of them'

        Args:
            description (str): description of the overall set of validations (TODO:  support multiple descriptions)
            fn_and_columns_arr (List[Tuple[str, List[DataFrame -> Tuple[bool, dict[str, Any]]]]]:  while this is a
            relatively complex type, what it amounts to is 'a list of pairs of columns and the functions to run on them'
            resulting_exception (type): the response to generate if validation fails. Subclass of
                                        ConstraintWithMetadataException
            raise_or_typecheck (Optional[bool]):  whether to raise an exception (true) or a failed typecheck (false)
            type_for_internal (Optional[type]): what type to use for internal validators.  Subclass of
                                                ConstraintWithMetadata
            name (Optional[str]): what to call the constraint, defaults to the class name.
    """

    def __init__(
        self,
        description,
        fn_and_columns_arr,
        resulting_exception,
        raise_or_typecheck=True,
        type_for_internal=ColumnConstraintWithMetadata,
        name=None,
    ):
        self.column_to_fn_dict = defaultdict(list)
        for (column, fn_list) in fn_and_columns_arr:
            self.column_to_fn_dict[column].extend(fn_list)

        def validation_fn(data, *args, **kwargs):
            metadict = defaultdict(dict)
            truthparam = True
            for column, fn_arr in self.column_to_fn_dict.items():
                for fn in fn_arr:
                    # TODO:  do this more effectively
                    new_validator = type_for_internal(
                        fn.__doc__, fn, ColumnWithMetadataException, raise_or_typecheck=False
                    )
                    result = new_validator.validate(
                        DataFrame(data[column]), column, *args, **kwargs
                    )
                    result_val = result.success
                    if result_val:
                        continue
                    result_dict = result.metadata_entries[0].entry_data.data
                    truthparam = truthparam and result_val
                    for key in result_dict.keys():
                        if 'constraint' not in key:
                            if key == 'expected':
                                new_key = 'expectation'
                                result_dict[key] = result_dict[key].replace('returns', '').strip()
                                if column not in metadict[new_key] or new_key not in metadict:
                                    metadict[new_key][column] = dict()
                                metadict[new_key][column][fn.__name__] = result_dict[key]
                            else:
                                if column not in metadict[key] or key not in metadict:
                                    metadict[key][column] = dict()
                                if isinstance(result_dict[key], dict):
                                    metadict[key][column][fn.__name__] = result_dict[key][column]
                                else:
                                    metadict[key][column][fn.__name__] = 'a violation'
            return truthparam, metadict

        super(MultiColumnConstraintWithMetadata, self).__init__(
            description,
            validation_fn,
            resulting_exception,
            raise_or_typecheck=raise_or_typecheck,
            name=name,
        )

    def validate(self, data, *args, **kwargs):
        return ConstraintWithMetadata.validate(self, data, *args, **kwargs)


class MultiAggregateConstraintWithMetadata(MultiColumnConstraintWithMetadata):
    """
        This class is similar to multicolumn, but takes in functions that operate on the whole column at once
        rather than ones that operate on each value --
        consider this similar to the difference between apply-map and apply aggregate.
    """

    def __init__(
        self,
        description,
        fn_and_columns_arr,
        resulting_exception,
        raise_or_typecheck=True,
        name=None,
    ):
        super(MultiAggregateConstraintWithMetadata, self).__init__(
            description,
            fn_and_columns_arr,
            resulting_exception,
            raise_or_typecheck=raise_or_typecheck,
            type_for_internal=ColumnAggregateConstraintWithMetadata,
            name=name,
        )


class ColumnRangeConstraintWithMetadata(ColumnConstraintWithMetadata):
    def __init__(self, minim=None, maxim=None, columns=None, raise_or_typecheck=True):
        self.name = self.__class__.__name__
        if minim is None:
            minim = -1 * (sys.maxsize - 1)
        if maxim is None:
            maxim = sys.maxsize

        def validation_fn(x):
            return ((x <= maxim) and (x >= minim), {})

        description = "Confirms values are between {} and {}".format(minim, maxim)
        super(ColumnRangeConstraintWithMetadata, self).__init__(
            description=description,
            validation_fn=validation_fn,
            resulting_exception=ColumnWithMetadataException,
            raise_or_typecheck=raise_or_typecheck,
        )
        self.columns = columns

    def validate(self, data, *args, **kwargs):
        if self.columns is None:
            self.columns = list(data.columns)
        self.columns.extend(args)
        return super(ColumnRangeConstraintWithMetadata, self).validate(
            data, *self.columns, **kwargs
        )


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
    A column constraint that ensures all values in a pandas column are between the lower and upper
    bound [inclusive].

    Args:
        min_value (Union[int, float, datetime.datetime]): The lower bound.
        max_value (Union[int, float, datetime.datetime]): The upper bound.
        ignore_missing_vals (bool): If true, this constraint will enforce the constraint on non
            missing values.
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
