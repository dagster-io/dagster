from typing import Mapping, Optional, Sequence, Union

from pydantic.dataclasses import dataclass

from dagster._annotations import PublicAttr, experimental, public
from dagster._serdes.serdes import whitelist_for_serdes

# ########################
# ##### TABLE RECORD
# ########################


@experimental
@whitelist_for_serdes
@dataclass(frozen=True, config=dict(extra="forbid"))
class TableRecord:
    """Represents one record in a table. Field keys are arbitrary strings-- field values must be
    strings, integers, floats, or bools.
    """

    data: PublicAttr[Mapping[str, Union[str, int, float, bool]]]


# ########################
# ##### TABLE CONSTRAINTS
# ########################


@whitelist_for_serdes
@dataclass(frozen=True, config=dict(extra="forbid"))
class TableConstraints:
    """Descriptor for "table-level" constraints. Presently only one property,
    `other` is supported. This contains strings describing arbitrary
    table-level constraints. A table-level constraint is a constraint defined
    in terms of multiple columns (e.g. col_A > col_B) or in terms of rows.

    Args:
        other (List[str]): Descriptions of arbitrary table-level constraints.
    """

    other: PublicAttr[Sequence[str]]


_DEFAULT_TABLE_CONSTRAINTS = TableConstraints(other=[])

# ########################
# ##### TABLE COLUMN CONSTRAINTS
# ########################


@whitelist_for_serdes
@dataclass(frozen=True, config=dict(extra="forbid"))
class TableColumnConstraints:
    """Descriptor for a table column's constraints. Nullability and uniqueness are specified with
    boolean properties. All other constraints are described using arbitrary strings under the
    `other` property.

    Args:
        nullable (Optional[bool]): If true, this column can hold null values.
        unique (Optional[bool]): If true, all values in this column must be unique.
        other (Sequence[str]): Descriptions of arbitrary column-level constraints
            not expressible by the predefined properties.
    """

    nullable: PublicAttr[bool] = True
    unique: PublicAttr[bool] = False
    other: PublicAttr[Optional[Sequence[str]]] = None


_DEFAULT_TABLE_COLUMN_CONSTRAINTS = TableColumnConstraints()


# ########################
# ##### TABLE COLUMN
# ########################


@whitelist_for_serdes
@dataclass(frozen=True, config=dict(extra="forbid"))
class TableColumn:
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
    """

    name: PublicAttr[str]
    type: PublicAttr[str] = "string"
    description: PublicAttr[Optional[str]] = None
    constraints: PublicAttr[TableColumnConstraints] = _DEFAULT_TABLE_COLUMN_CONSTRAINTS


# ########################
# ##### TABLE SCHEMA
# ########################


@whitelist_for_serdes
@dataclass(frozen=True, config=dict(extra="forbid"))
class TableSchema:
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
                            required = True,
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

    columns: PublicAttr[Sequence[TableColumn]]
    constraints: PublicAttr[TableConstraints] = _DEFAULT_TABLE_CONSTRAINTS

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
