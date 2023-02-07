from dagster import (
    DagsterInvariantViolationError,
    _check as check,
)
from pandas import DataFrame, Timestamp
from pandas.core.dtypes.common import (
    is_bool_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_numeric_dtype,
    is_string_dtype,
)

from dagster_pandas.constraints import (
    CategoricalColumnConstraint,
    ColumnDTypeFnConstraint,
    ColumnDTypeInSetConstraint,
    Constraint,
    ConstraintViolationException,
    DataFrameConstraint,
    InRangeColumnConstraint,
    NonNullableColumnConstraint,
    UniqueColumnConstraint,
)

PANDAS_NUMERIC_TYPES = {"int64", "float"}


def _construct_keyword_constraints(non_nullable, unique, ignore_missing_vals):
    non_nullable = check.bool_param(non_nullable, "exists")
    unique = check.bool_param(unique, "unique")
    ignore_missing_vals = check.bool_param(ignore_missing_vals, "ignore_missing_vals")
    if non_nullable and ignore_missing_vals:
        raise DagsterInvariantViolationError(
            "PandasColumn cannot have a non-null constraint while also ignore missing values"
        )
    constraints = []
    if non_nullable:
        constraints.append(NonNullableColumnConstraint())
    if unique:
        constraints.append(UniqueColumnConstraint(ignore_missing_vals=ignore_missing_vals))
    return constraints


class PandasColumn:
    """
    The main API for expressing column level schemas and constraints for your custom dataframe
    types.

    Args:
        name (str): Name of the column. This must match up with the column name in the dataframe you
            expect to receive.
        is_required (Optional[bool]): Flag indicating the optional/required presence of the column.
            If th column exists, the validate function will validate the column. Defaults to True.
        constraints (Optional[List[Constraint]]): List of constraint objects that indicate the
            validation rules for the pandas column.
    """

    def __init__(self, name, constraints=None, is_required=None):
        self.name = check.str_param(name, "name")
        self.is_required = check.opt_bool_param(is_required, "is_required", default=True)
        self.constraints = check.opt_list_param(constraints, "constraints", of_type=Constraint)

    def validate(self, dataframe):
        if self.name not in dataframe.columns:
            # Ignore validation if column is missing from dataframe and is not required
            if self.is_required:
                raise ConstraintViolationException(
                    "Required column {column_name} not in dataframe with columns"
                    " {dataframe_columns}".format(
                        column_name=self.name, dataframe_columns=dataframe.columns
                    )
                )
        else:
            for constraint in self.constraints:
                constraint.validate(dataframe, self.name)

    @staticmethod
    def exists(name, non_nullable=False, unique=False, ignore_missing_vals=False, is_required=None):
        """
        Simple constructor for PandasColumns that expresses existence constraints.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
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
            constraints=_construct_keyword_constraints(
                non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
            ),
            is_required=is_required,
        )

    @staticmethod
    def boolean_column(
        name, non_nullable=False, unique=False, ignore_missing_vals=False, is_required=None
    ):
        """
        Simple constructor for PandasColumns that expresses boolean constraints on boolean dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
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
            constraints=[ColumnDTypeFnConstraint(is_bool_dtype)]
            + _construct_keyword_constraints(
                non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
            ),
            is_required=is_required,
        )

    @staticmethod
    def numeric_column(
        name,
        min_value=-float("inf"),
        max_value=float("inf"),
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False,
        is_required=None,
    ):
        """
        Simple constructor for PandasColumns that expresses numeric constraints numeric dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
            min_value (Optional[Union[int,float]]): The lower bound for values you expect in this column. Defaults to -float('inf')
            max_value (Optional[Union[int,float]]): The upper bound for values you expect in this column. Defaults to float('inf')
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
                ColumnDTypeFnConstraint(is_numeric_dtype),
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

    @staticmethod
    def integer_column(
        name,
        min_value=-float("inf"),
        max_value=float("inf"),
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False,
        is_required=None,
    ):
        """
        Simple constructor for PandasColumns that expresses numeric constraints on integer dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
            min_value (Optional[Union[int,float]]): The lower bound for values you expect in this column. Defaults to -float('inf')
            max_value (Optional[Union[int,float]]): The upper bound for values you expect in this column. Defaults to float('inf')
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
                ColumnDTypeFnConstraint(is_integer_dtype),
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

    @staticmethod
    def float_column(
        name,
        min_value=-float("inf"),
        max_value=float("inf"),
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False,
        is_required=None,
    ):
        """
        Simple constructor for PandasColumns that expresses numeric constraints on float dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
            min_value (Optional[Union[int,float]]): The lower bound for values you expect in this column. Defaults to -float('inf')
            max_value (Optional[Union[int,float]]): The upper bound for values you expect in this column. Defaults to float('inf')
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
                ColumnDTypeFnConstraint(is_float_dtype),
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

    @staticmethod
    def datetime_column(
        name,
        min_datetime=Timestamp.min,
        max_datetime=Timestamp.max,
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False,
        is_required=None,
        tz=None,
    ):
        """
        Simple constructor for PandasColumns that expresses datetime constraints on 'datetime64[ns]' dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
            min_datetime (Optional[Union[int,float]]): The lower bound for values you expect in this column.
                Defaults to pandas.Timestamp.min.
            max_datetime (Optional[Union[int,float]]): The upper bound for values you expect in this column.
                Defaults to pandas.Timestamp.max.
            non_nullable (Optional[bool]): If true, this column will enforce a constraint that all values in the column
                ought to be non null values.
            unique (Optional[bool]): If true, this column will enforce a uniqueness constraint on the column values.
            ignore_missing_vals (Optional[bool]): A flag that is passed into most constraints. If true, the constraint will
                only evaluate non-null data. Ignore_missing_vals and non_nullable cannot both be True.
            is_required (Optional[bool]): Flag indicating the optional/required presence of the column.
                If the column exists the validate function will validate the column. Default to True.
            tz (Optional[str]): Required timezone for values eg: tz='UTC', tz='Europe/Dublin', tz='US/Eastern'.
                Defaults to None, meaning naive datetime values.
        """
        if tz is None:
            datetime_constraint = ColumnDTypeInSetConstraint({"datetime64[ns]"})
        else:
            datetime_constraint = ColumnDTypeInSetConstraint({f"datetime64[ns, {tz}]"})
            # One day more/less than absolute min/max to prevent OutOfBoundsDatetime errors when converting min/max to be tz aware
            if min_datetime.tz_localize(None) == Timestamp.min:
                min_datetime = Timestamp("1677-09-22 00:12:43.145225Z")
            if max_datetime.tz_localize(None) == Timestamp.max:
                max_datetime = Timestamp("2262-04-10 23:47:16.854775807Z")
            # Convert bounds to same tz
            if Timestamp(min_datetime).tz is None:
                min_datetime = Timestamp(min_datetime).tz_localize(tz)
            if Timestamp(max_datetime).tz is None:
                max_datetime = Timestamp(max_datetime).tz_localize(tz)

        return PandasColumn(
            name=check.str_param(name, "name"),
            constraints=[
                datetime_constraint,
                InRangeColumnConstraint(
                    min_datetime, max_datetime, ignore_missing_vals=ignore_missing_vals
                ),
            ]
            + _construct_keyword_constraints(
                non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
            ),
            is_required=is_required,
        )

    @staticmethod
    def string_column(
        name, non_nullable=False, unique=False, ignore_missing_vals=False, is_required=None
    ):
        """
        Simple constructor for PandasColumns that expresses constraints on string dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
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
            constraints=[ColumnDTypeFnConstraint(is_string_dtype)]
            + _construct_keyword_constraints(
                non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
            ),
            is_required=is_required,
        )

    @staticmethod
    def categorical_column(
        name,
        categories,
        of_types=frozenset({"category", "object"}),
        non_nullable=False,
        unique=False,
        ignore_missing_vals=False,
        is_required=None,
    ):
        """
        Simple constructor for PandasColumns that expresses categorical constraints on specified dtypes.

        Args:
            name (str): Name of the column. This must match up with the column name in the dataframe you
                expect to receive.
            categories (List[Any]): The valid set of buckets that all values in the column must match.
            of_types (Optional[Union[str, Set[str]]]): The expected dtype[s] that your categories and values must
                abide by.
            non_nullable (Optional[bool]): If true, this column will enforce a constraint that all values in
                the column ought to be non null values.
            unique (Optional[bool]): If true, this column will enforce a uniqueness constraint on the column values.
            ignore_missing_vals (Optional[bool]): A flag that is passed into most constraints. If true, the
                constraint will only evaluate non-null data. Ignore_missing_vals and non_nullable cannot both be True.
            is_required (Optional[bool]): Flag indicating the optional/required presence of the column.
                If the column exists the validate function will validate the column. Default to True.
        """
        of_types = {of_types} if isinstance(of_types, str) else of_types
        return PandasColumn(
            name=check.str_param(name, "name"),
            constraints=[
                ColumnDTypeInSetConstraint(of_types),
                CategoricalColumnConstraint(categories, ignore_missing_vals=ignore_missing_vals),
            ]
            + _construct_keyword_constraints(
                non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
            ),
            is_required=is_required,
        )


def validate_constraints(dataframe, pandas_columns=None, dataframe_constraints=None):
    dataframe = check.inst_param(dataframe, "dataframe", DataFrame)
    pandas_columns = check.opt_list_param(
        pandas_columns, "column_constraints", of_type=PandasColumn
    )
    dataframe_constraints = check.opt_list_param(
        dataframe_constraints, "dataframe_constraints", of_type=DataFrameConstraint
    )

    if pandas_columns:
        for column in pandas_columns:
            column.validate(dataframe)

    if dataframe_constraints:
        for dataframe_constraint in dataframe_constraints:
            dataframe_constraint.validate(dataframe)
