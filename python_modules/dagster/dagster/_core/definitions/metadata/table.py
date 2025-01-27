from collections.abc import Mapping, Sequence
from typing import NamedTuple, Optional, Union

import dagster._check as check
from dagster._annotations import PublicAttr, experimental, public
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._serdes.serdes import whitelist_for_serdes

# ########################
# ##### TABLE RECORD
# ########################


@experimental
@whitelist_for_serdes
class TableRecord(
    NamedTuple(
        "TableRecord", [("data", PublicAttr[Mapping[str, Optional[Union[str, int, float, bool]]]])]
    )
):
    """Represents one record in a table. Field keys are arbitrary strings-- field values must be
    strings, integers, floats, or bools.
    """

    def __new__(cls, data: Mapping[str, Optional[Union[str, int, float, bool]]]):
        check.dict_param(
            data,
            "data",
            value_type=(str, float, int, bool, type(None)),
            additional_message="Record fields must be one of types: (str, float, int, bool)",
        )
        return super().__new__(cls, data=data)


# ########################
# ##### TABLE CONSTRAINTS
# ########################


@whitelist_for_serdes
class TableConstraints(
    NamedTuple(
        "TableConstraints",
        [
            ("other", PublicAttr[Sequence[str]]),
        ],
    )
):
    """Descriptor for "table-level" constraints. Presently only one property,
    `other` is supported. This contains strings describing arbitrary
    table-level constraints. A table-level constraint is a constraint defined
    in terms of multiple columns (e.g. col_A > col_B) or in terms of rows.

    Args:
        other (List[str]): Descriptions of arbitrary table-level constraints.
    """

    def __new__(
        cls,
        other: Sequence[str],
    ):
        return super().__new__(
            cls,
            other=check.sequence_param(other, "other", of_type=str),
        )


_DEFAULT_TABLE_CONSTRAINTS = TableConstraints(other=[])

# ########################
# ##### TABLE COLUMN CONSTRAINTS
# ########################


@whitelist_for_serdes
class TableColumnConstraints(
    NamedTuple(
        "TableColumnConstraints",
        [
            ("nullable", PublicAttr[bool]),
            ("unique", PublicAttr[bool]),
            ("other", PublicAttr[Optional[Sequence[str]]]),
        ],
    )
):
    """Descriptor for a table column's constraints. Nullability and uniqueness are specified with
    boolean properties. All other constraints are described using arbitrary strings under the
    `other` property.

    Args:
        nullable (Optional[bool]): If true, this column can hold null values.
        unique (Optional[bool]): If true, all values in this column must be unique.
        other (List[str]): Descriptions of arbitrary column-level constraints
            not expressible by the predefined properties.
    """

    def __new__(
        cls,
        nullable: bool = True,
        unique: bool = False,
        other: Optional[Sequence[str]] = None,
    ):
        return super().__new__(
            cls,
            nullable=check.bool_param(nullable, "nullable"),
            unique=check.bool_param(unique, "unique"),
            other=check.opt_sequence_param(other, "other"),
        )


_DEFAULT_TABLE_COLUMN_CONSTRAINTS = TableColumnConstraints()

# ########################
# ##### TABLE COLUMN
# ########################


@whitelist_for_serdes(skip_when_empty_fields={"tags"})
class TableColumn(
    NamedTuple(
        "TableColumn",
        [
            ("name", PublicAttr[str]),
            ("type", PublicAttr[str]),
            ("description", PublicAttr[Optional[str]]),
            ("constraints", PublicAttr[TableColumnConstraints]),
            ("tags", PublicAttr[Mapping[str, str]]),
        ],
    )
):
    """Descriptor for a table column. The only property that must be specified
    by the user is `name`. If no `type` is specified, `string` is assumed. If
    no `constraints` are specified, the column is assumed to be nullable
    (i.e. `required = False`) and have no other constraints beyond the data type.

    Args:
        name (List[str]): Descriptions of arbitrary table-level constraints.
        type (Optional[str]): The type of the column. Can be an arbitrary
            string. Defaults to `"string"`.
        description (Optional[str]): Description of this column. Defaults to `None`.
        constraints (Optional[TableColumnConstraints]): Column-level constraints.
            If unspecified, column is nullable with no constraints.
        tags (Optional[Mapping[str, str]]): Tags for filtering or organizing columns.
    """

    def __new__(
        cls,
        name: str,
        type: str = "string",  # noqa: A002
        description: Optional[str] = None,
        constraints: Optional[TableColumnConstraints] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        return super().__new__(
            cls,
            name=check.str_param(name, "name"),
            type=check.str_param(type, "type"),
            description=check.opt_str_param(description, "description"),
            constraints=check.opt_inst_param(
                constraints,
                "constraints",
                TableColumnConstraints,
                default=_DEFAULT_TABLE_COLUMN_CONSTRAINTS,
            ),
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
        )


# ########################
# ##### TABLE SCHEMA
# ########################


@whitelist_for_serdes
class TableSchema(
    NamedTuple(
        "TableSchema",
        [
            ("columns", PublicAttr[Sequence[TableColumn]]),
            ("constraints", PublicAttr[TableConstraints]),
        ],
    )
):
    """Representation of a schema for tabular data.

    Schema is composed of two parts:

    - A required list of columns (`TableColumn`). Each column specifies a
      `name`, `type`, set of `constraints`, and (optional) `description`. `type`
      defaults to `string` if unspecified. Column constraints
      (`TableColumnConstraints`) consist of boolean properties `unique` and
      `nullable`, as well as a list of strings `other` containing string
      descriptions of all additional constraints (e.g. `"<= 5"`).
    - An optional list of table-level constraints (`TableConstraints`). A
      table-level constraint cannot be expressed in terms of a single column,
      e.g. col a > col b. Presently, all table-level constraints must be
      expressed as strings under the `other` attribute of a `TableConstraints`
      object.

    .. code-block:: python

            # example schema
            TableSchema(
                constraints = TableConstraints(
                    other = [
                        "foo > bar",
                    ],
                ),
                columns = [
                    TableColumn(
                        name = "foo",
                        type = "string",
                        description = "Foo description",
                        constraints = TableColumnConstraints(
                            nullable = False,
                            other = [
                                "starts with the letter 'a'",
                            ],
                        ),
                    ),
                    TableColumn(
                        name = "bar",
                        type = "string",
                    ),
                    TableColumn(
                        name = "baz",
                        type = "custom_type",
                        constraints = TableColumnConstraints(
                            unique = True,
                        )
                    ),
                ],
            )

    Args:
        columns (List[TableColumn]): The columns of the table.
        constraints (Optional[TableConstraints]): The constraints of the table.
    """

    def __new__(
        cls,
        columns: Sequence[TableColumn],
        constraints: Optional[TableConstraints] = None,
    ):
        return super().__new__(
            cls,
            columns=check.sequence_param(columns, "columns", of_type=TableColumn),
            constraints=check.opt_inst_param(
                constraints, "constraints", TableConstraints, default=_DEFAULT_TABLE_CONSTRAINTS
            ),
        )

    @public
    @staticmethod
    def from_name_type_dict(name_type_dict: Mapping[str, str]):
        """Constructs a TableSchema from a dictionary whose keys are column names and values are the
        names of data types of those columns.
        """
        return TableSchema(
            columns=[
                TableColumn(name=name, type=type_str) for name, type_str in name_type_dict.items()
            ]
        )


# ###########################
# ##### TABLE COLUMN LINEAGE
# ###########################


@experimental(emit_runtime_warning=False)
@whitelist_for_serdes
class TableColumnDep(
    NamedTuple(
        "_TableColumnDep",
        [
            ("asset_key", PublicAttr[CoercibleToAssetKey]),
            ("column_name", PublicAttr[str]),
        ],
    )
):
    """Object representing an identifier for a column in an asset."""

    def __new__(
        cls,
        asset_key: CoercibleToAssetKey,
        column_name: str,
    ):
        return super().__new__(
            cls,
            asset_key=AssetKey.from_coercible(asset_key),
            column_name=check.str_param(column_name, "column_name"),
        )


@experimental
@whitelist_for_serdes
class TableColumnLineage(
    NamedTuple(
        "_TableSpec",
        [
            ("deps_by_column", PublicAttr[Mapping[str, Sequence[TableColumnDep]]]),
        ],
    )
):
    """Represents the lineage of column outputs to column inputs for a tabular asset.

    Args:
        deps_by_column (Mapping[str, Sequence[TableColumnDep]]): A mapping from column names to
            the columns that the column depends on.

    Examples:
        Defining column lineage at materialization time, where the resulting asset has two columns,
        ``new_column_foo`` and ``new_column_qux``. The first column, ``new_column_foo``, depends on
        ``column_bar`` in ``source_bar`` and ``column_baz`` in ``source_baz``. The second column,
        ``new_column_qux``, depends on ``column_quuz`` in ``source_bar``.

        .. code-block:: python

            from dagster import (
                AssetKey,
                MaterializeResult,
                TableColumnDep,
                TableColumnLineage,
                asset,
            )


            @asset(deps=[AssetKey("source_bar"), AssetKey("source_baz")])
            def my_asset():
                yield MaterializeResult(
                    metadata={
                        "dagster/column_lineage": TableColumnLineage(
                            deps_by_column={
                                "new_column_foo": [
                                    TableColumnDep(
                                        asset_key=AssetKey("source_bar"),
                                        column_name="column_bar",
                                    ),
                                    TableColumnDep(
                                        asset_key=AssetKey("source_baz"),
                                        column_name="column_baz",
                                    ),
                                ],
                                "new_column_qux": [
                                    TableColumnDep(
                                        asset_key=AssetKey("source_bar"),
                                        column_name="column_quuz",
                                    ),
                                ],
                            }
                        )
                    }
                )
    """

    def __new__(cls, deps_by_column: Mapping[str, Sequence[TableColumnDep]]):
        deps_by_column = check.mapping_param(
            deps_by_column, "deps_by_column", key_type=str, value_type=list
        )

        sorted_deps_by_column = {}
        for column, deps in deps_by_column.items():
            sorted_deps_by_column[column] = sorted(
                deps, key=lambda dep: (dep.asset_key, dep.column_name)
            )

            check.invariant(
                len(deps) == len(set((dep.asset_key, dep.column_name) for dep in deps)),
                f"The deps for column `{column}` must be unique by asset key and column name.",
            )

        return super().__new__(cls, deps_by_column=sorted_deps_by_column)
