import pandas as pd
from dagster_pandas.constraints import (
    ColumnDTypeFnConstraint,
    ColumnDTypeInSetConstraint,
    ConstraintViolationException,
)
from dagster_pandas.validation import PandasColumn, validate_constraints

from dagster import (
    AssetMaterialization,
    DagsterInvariantViolationError,
    DagsterType,
    Field,
    MetadataEntry,
    StringSource,
    TypeCheck,
)
from dagster import _check as check
from dagster import dagster_type_loader, dagster_type_materializer
from dagster._check import CheckError
from dagster.config.field_utils import Selector
from dagster.core.definitions.metadata import normalize_metadata
from dagster.core.errors import DagsterInvalidMetadata
from dagster.utils import dict_without_keys
from dagster.utils.backcompat import experimental

CONSTRAINT_BLACKLIST = {ColumnDTypeFnConstraint, ColumnDTypeInSetConstraint}


@dagster_type_materializer(
    Selector(
        {
            "csv": {
                "path": StringSource,
                "sep": Field(StringSource, is_required=False, default_value=","),
            },
            "parquet": {"path": StringSource},
            "table": {"path": StringSource},
            "pickle": {"path": StringSource},
        },
    )
)
def dataframe_materializer(_context, config, pandas_df):
    check.inst_param(pandas_df, "pandas_df", pd.DataFrame)
    file_type, file_options = list(config.items())[0]

    if file_type == "csv":
        path = file_options["path"]
        pandas_df.to_csv(path, index=False, **dict_without_keys(file_options, "path"))
    elif file_type == "parquet":
        pandas_df.to_parquet(file_options["path"])
    elif file_type == "table":
        pandas_df.to_csv(file_options["path"], sep="\t", index=False)
    elif file_type == "pickle":
        pandas_df.to_pickle(file_options["path"])
    else:
        check.failed("Unsupported file_type {file_type}".format(file_type=file_type))

    return AssetMaterialization.file(file_options["path"])


@dagster_type_loader(
    Selector(
        {
            "csv": {
                "path": StringSource,
                "sep": Field(StringSource, is_required=False, default_value=","),
            },
            "parquet": {"path": StringSource},
            "table": {"path": StringSource},
            "pickle": {"path": StringSource},
        },
    )
)
def dataframe_loader(_context, config):
    file_type, file_options = list(config.items())[0]

    if file_type == "csv":
        path = file_options["path"]
        return pd.read_csv(path, **dict_without_keys(file_options, "path"))
    elif file_type == "parquet":
        return pd.read_parquet(file_options["path"])
    elif file_type == "table":
        return pd.read_csv(file_options["path"], sep="\t")
    elif file_type == "pickle":
        return pd.read_pickle(file_options["path"])
    else:
        raise DagsterInvariantViolationError(
            "Unsupported file_type {file_type}".format(file_type=file_type)
        )


def df_type_check(_, value):
    if not isinstance(value, pd.DataFrame):
        return TypeCheck(success=False)
    return TypeCheck(
        success=True,
        metadata_entries=[
            MetadataEntry("row_count", value=str(len(value))),
            # string cast columns since they may be things like datetime
            MetadataEntry("metadata", value={"columns": list(map(str, value.columns))}),
        ],
    )


DataFrame = DagsterType(
    name="PandasDataFrame",
    description="""Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns).
    See http://pandas.pydata.org/""",
    loader=dataframe_loader,
    materializer=dataframe_materializer,
    type_check_fn=df_type_check,
)


def _construct_constraint_list(constraints):
    def add_bullet(constraint_list, constraint_description):
        return constraint_list + "+ {constraint_description}\n".format(
            constraint_description=constraint_description
        )

    constraint_list = ""
    for constraint in constraints:
        if constraint.__class__ not in CONSTRAINT_BLACKLIST:
            constraint_list = add_bullet(constraint_list, constraint.markdown_description)
    return constraint_list


def _build_column_header(column_name, constraints):
    header = "**{column_name}**".format(column_name=column_name)
    for constraint in constraints:
        if isinstance(constraint, ColumnDTypeInSetConstraint):
            dtypes_tuple = tuple(constraint.expected_dtype_set)
            return header + ": `{expected_dtypes}`".format(
                expected_dtypes=dtypes_tuple if len(dtypes_tuple) > 1 else dtypes_tuple[0]
            )
        elif isinstance(constraint, ColumnDTypeFnConstraint):
            return header + ": Validator `{expected_dtype_fn}`".format(
                expected_dtype_fn=constraint.type_fn.__name__
            )
    return header


def create_dagster_pandas_dataframe_description(description, columns):
    title = "\n".join([description, "### Columns", ""])
    buildme = title
    for column in columns:
        buildme += "{}\n{}\n".format(
            _build_column_header(column.name, column.constraints),
            _construct_constraint_list(column.constraints),
        )
    return buildme


def create_dagster_pandas_dataframe_type(
    name,
    description=None,
    columns=None,
    event_metadata_fn=None,
    dataframe_constraints=None,
    loader=None,
    materializer=None,
):
    """
    Constructs a custom pandas dataframe dagster type.

    Args:
        name (str): Name of the dagster pandas type.
        description (Optional[str]): A markdown-formatted string, displayed in tooling.
        columns (Optional[List[PandasColumn]]): A list of :py:class:`~dagster.PandasColumn` objects
            which express dataframe column schemas and constraints.
        event_metadata_fn (Optional[Callable[[], Union[Dict[str, Union[str, float, int, Dict, MetadataValue]], List[MetadataEntry]]]]):
            A callable which takes your dataframe and returns a dict with string label keys and
            MetadataValue values. Can optionally return a List[MetadataEntry].
        dataframe_constraints (Optional[List[DataFrameConstraint]]): A list of objects that inherit from
            :py:class:`~dagster.DataFrameConstraint`. This allows you to express dataframe-level constraints.
        loader (Optional[DagsterTypeLoader]): An instance of a class that
            inherits from :py:class:`~dagster.DagsterTypeLoader`. If None, we will default
            to using `dataframe_loader`.
        materializer (Optional[DagsterTypeMaterializer]): An instance of a class
            that inherits from :py:class:`~dagster.DagsterTypeMaterializer`. If None, we will
            default to using `dataframe_materializer`.
    """
    # We allow for the plugging in of dagster_type_loaders/materializers so that
    # Users can load and materialize their custom dataframes via configuration their own way if the default
    # configs don't suffice. This is purely optional.
    check.str_param(name, "name")
    event_metadata_fn = check.opt_callable_param(event_metadata_fn, "event_metadata_fn")
    description = create_dagster_pandas_dataframe_description(
        check.opt_str_param(description, "description", default=""),
        check.opt_list_param(columns, "columns", of_type=PandasColumn),
    )

    def _dagster_type_check(_, value):
        if not isinstance(value, pd.DataFrame):
            return TypeCheck(
                success=False,
                description="Must be a pandas.DataFrame. Got value of type. {type_name}".format(
                    type_name=type(value).__name__
                ),
            )

        try:
            validate_constraints(
                value, pandas_columns=columns, dataframe_constraints=dataframe_constraints
            )
        except ConstraintViolationException as e:
            return TypeCheck(success=False, description=str(e))

        return TypeCheck(
            success=True,
            metadata_entries=_execute_summary_stats(name, value, event_metadata_fn)
            if event_metadata_fn
            else None,
        )

    return DagsterType(
        name=name,
        type_check_fn=_dagster_type_check,
        loader=loader if loader else dataframe_loader,
        materializer=materializer if materializer else dataframe_materializer,
        description=description,
    )


@experimental
def create_structured_dataframe_type(
    name,
    description=None,
    columns_validator=None,
    columns_aggregate_validator=None,
    dataframe_validator=None,
    loader=None,
    materializer=None,
):
    """

    Args:
        name (str): the name of the new type
        description (Optional[str]): the description of the new type
        columns_validator (Optional[Union[ColumnConstraintWithMetadata, MultiColumnConstraintWithMetadata]]):
                    what column-level row by row validation you want to have applied.
                    Leave empty for no column-level row by row validation.
        columns_aggregate_validator (Optional[Union[ColumnAggregateConstraintWithMetadata,
                                    MultiAggregateConstraintWithMetadata]]):
                    what column-level aggregate validation you want to have applied,
                    Leave empty for no column-level aggregate validation.
        dataframe_validator (Optional[Union[ConstraintWithMetadata, MultiConstraintWithMetadata]]):
                    what dataframe-wide validation you want to have applied.
                    Leave empty for no dataframe-wide validation.
        loader (Optional[DagsterTypeLoader]): An instance of a class that
            inherits from :py:class:`~dagster.DagsterTypeLoader`. If None, we will default
            to using `dataframe_loader`.
        materializer (Optional[DagsterTypeMaterializer]): An instance of a class
            that inherits from :py:class:`~dagster.DagsterTypeMaterializer`. If None, we will
            default to using `dataframe_materializer`.

    Returns:
        a DagsterType with the corresponding name and packaged validation.

    """

    def _dagster_type_check(_, value):
        if not isinstance(value, pd.DataFrame):
            return TypeCheck(
                success=False,
                description="Must be a pandas.DataFrame. Got value of type. {type_name}".format(
                    type_name=type(value).__name__
                ),
            )
        individual_result_dict = {}

        if dataframe_validator is not None:
            individual_result_dict["dataframe"] = dataframe_validator.validate(value)
        if columns_validator is not None:
            individual_result_dict["columns"] = columns_validator.validate(value)

        if columns_aggregate_validator is not None:
            individual_result_dict["column-aggregates"] = columns_aggregate_validator.validate(
                value
            )

        typechecks_succeeded = True
        metadata = []
        overall_description = "Failed Constraints: {}"
        constraint_clauses = []
        for key, result in individual_result_dict.items():
            result_val = result.success
            if result_val:
                continue
            typechecks_succeeded = typechecks_succeeded and result_val
            result_dict = result.metadata_entries[0].entry_data.data
            metadata.append(
                MetadataEntry(
                    "{}-constraint-metadata".format(key),
                    value=result_dict,
                )
            )
            constraint_clauses.append("{} failing constraints, {}".format(key, result.description))
        # returns aggregates, then column, then dataframe
        return TypeCheck(
            success=typechecks_succeeded,
            description=overall_description.format(constraint_clauses),
            metadata_entries=sorted(metadata, key=lambda x: x.label),
        )

    description = check.opt_str_param(description, "description", default="")
    return DagsterType(
        name=name,
        type_check_fn=_dagster_type_check,
        loader=loader if loader else dataframe_loader,
        materializer=materializer if loader else dataframe_materializer,
        description=description,
    )


def _execute_summary_stats(type_name, value, event_metadata_fn):
    if not event_metadata_fn:
        return []

    metadata_or_metadata_entries = event_metadata_fn(value)

    invalid_message = (
        "The return value of the user-defined summary_statistics function for pandas "
        f"data frame type {type_name} returned {value}. This function must return "
        "Union[Dict[str, Union[str, float, int, Dict, MetadataValue]], List[MetadataEntry]]"
    )

    metadata = None
    metadata_entries = None

    if isinstance(metadata_or_metadata_entries, list):
        metadata_entries = metadata_or_metadata_entries
    elif isinstance(metadata_or_metadata_entries, dict):
        metadata = metadata_or_metadata_entries
    else:
        raise DagsterInvariantViolationError(invalid_message)

    try:
        return normalize_metadata(metadata, metadata_entries)
    except (DagsterInvalidMetadata, CheckError):
        raise DagsterInvariantViolationError(invalid_message)
