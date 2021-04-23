from dagster import EventMetadataEntry, TypeCheck


# start_custom_types_4_marker_0
def less_simple_data_frame_type_check(_, value):
    if not isinstance(value, list):
        return TypeCheck(
            success=False,
            description=(
                "LessSimpleDataFrame should be a list of dicts, got "
                "{type_}"
            ).format(type_=type(value)),
        )

    fields = [field for field in value[0].keys()]

    for i in range(len(value)):
        row = value[i]
        if not isinstance(row, dict):
            return TypeCheck(
                success=False,
                description=(
                    "LessSimpleDataFrame should be a list of dicts, "
                    "got {type_} for row {idx}"
                ).format(type_=type(row), idx=(i + 1)),
            )
        row_fields = [field for field in row.keys()]
        if fields != row_fields:
            return TypeCheck(
                success=False,
                description=(
                    "Rows in LessSimpleDataFrame should have the same fields, "
                    "got {actual} for row {idx}, expected {expected}"
                ).format(actual=row_fields, idx=(i + 1), expected=fields),
            )

    return TypeCheck(
        success=True,
        description="LessSimpleDataFrame summary statistics",
        metadata_entries=[
            EventMetadataEntry.text(
                str(len(value)),
                "n_rows",
                "Number of rows seen in the data frame",
            ),
            EventMetadataEntry.text(
                str(len(value[0].keys()) if len(value) > 0 else 0),
                "n_cols",
                "Number of columns seen in the data frame",
            ),
            EventMetadataEntry.text(
                str(list(value[0].keys()) if len(value) > 0 else []),
                "column_names",
                "Keys of columns seen in the data frame",
            ),
        ],
    )


# end_custom_types_4_marker_0
