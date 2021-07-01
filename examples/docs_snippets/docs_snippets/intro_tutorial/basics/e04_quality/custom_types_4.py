from dagster import TypeCheck


# start_custom_types_4_marker_0
def less_simple_data_frame_type_check(_, value):
    if not isinstance(value, list):
        return TypeCheck(
            success=False,
            description=f"LessSimpleDataFrame should be a list of dicts, got {type(value)}",
        )

    fields = [field for field in value[0].keys()]

    for i in range(len(value)):
        row = value[i]
        idx = i + 1
        if not isinstance(row, dict):
            return TypeCheck(
                success=False,
                description=(
                    f"LessSimpleDataFrame should be a list of dicts, got {type(row)} for row {idx}"
                ),
            )
        row_fields = [field for field in row.keys()]
        if fields != row_fields:
            return TypeCheck(
                success=False,
                description=(
                    f"Rows in LessSimpleDataFrame should have the same fields, got {row_fields} "
                    f"for row {idx}, expected {fields}"
                ),
            )

    return TypeCheck(
        success=True,
        description="LessSimpleDataFrame summary statistics",
        metadata={
            "n_rows": len(value),
            "n_cols": len(value[0].keys()) if len(value) > 0 else 0,
            "column_names": str(list(value[0].keys()) if len(value) > 0 else []),
        },
    )


# end_custom_types_4_marker_0
