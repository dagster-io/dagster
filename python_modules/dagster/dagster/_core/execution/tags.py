from dagster._config import Array, Field, ScalarUnion, Shape


def get_tag_concurrency_limits_config():
    return Field(
        config=Array(
            Shape(
                {
                    "key": str,
                    "value": Field(
                        ScalarUnion(
                            scalar_type=str,
                            non_scalar_schema=Shape({"applyLimitPerUniqueValue": bool}),
                        ),
                        is_required=False,
                    ),
                    "limit": Field(int),
                }
            )
        ),
        is_required=False,
        description=(
            "A set of limits that are applied to steps with particular tags. If a value is set, the"
            " limit is applied to only that key-value pair. If no value is set, the limit is"
            " applied across all values of that key. If the value is set to a dict with"
            " `applyLimitPerUniqueValue: true`, the limit will apply to the number of unique values"
            " for that key. Note that these limits are per run, not global."
        ),
    )
