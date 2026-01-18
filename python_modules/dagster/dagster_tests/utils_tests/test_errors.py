from dagster._serdes import serialize_value
from dagster._utils.error import SerializableErrorInfo, truncate_serialized_error


def test_truncate_serialized_error():
    normal_error = SerializableErrorInfo(
        "Short",
        stack=["Yep"],
        cls_name="Exception",
        cause=None,
        context=None,
    )

    assert len(serialize_value(normal_error)) <= 150

    long_string = "M" * 155
    large_inner_error = SerializableErrorInfo(
        long_string, stack=["F" * 60, "G" * 60, "H" * 60, "I" * 60], cls_name=None
    )

    other_large_inner_error = SerializableErrorInfo(
        "J" * 155,
        stack=["K" * 60, "L" * 60, "M" * 60, "N" * 60],
        cls_name=None,
        cause=large_inner_error,
        context=normal_error,
    )

    stack = ["A" * 60, "B" * 60, "C" * 60, "D" * 60]

    error = SerializableErrorInfo(
        long_string,
        stack,
        cls_name="MyClassName",
        cause=large_inner_error,
        context=other_large_inner_error,
    )

    assert truncate_serialized_error(
        error, field_size_limit=150, max_depth=0
    ) == SerializableErrorInfo(
        message="M" * 150 + " (TRUNCATED)",
        stack=["A" * 60, "B" * 60, "(TRUNCATED)"],
        cls_name="MyClassName",
        cause=SerializableErrorInfo(
            message="(Cause truncated due to size limitations)",
            stack=[],
            cls_name=None,
        ),
        context=SerializableErrorInfo(
            message="(Context truncated due to size limitations)",
            stack=[],
            cls_name=None,
        ),
    )

    # Test depth 1
    assert truncate_serialized_error(
        error, field_size_limit=150, max_depth=1
    ) == SerializableErrorInfo(
        message="M" * 150 + " (TRUNCATED)",
        stack=["A" * 60, "B" * 60, "(TRUNCATED)"],
        cls_name="MyClassName",
        cause=SerializableErrorInfo(
            message="M" * 150 + " (TRUNCATED)",
            stack=["F" * 60, "G" * 60, "(TRUNCATED)"],
            cls_name=None,
            cause=None,
            context=None,
        ),
        context=SerializableErrorInfo(
            message="J" * 150 + " (TRUNCATED)",
            stack=["K" * 60, "L" * 60, "(TRUNCATED)"],
            cls_name=None,
            cause=SerializableErrorInfo(
                message="(Cause truncated due to size limitations)",
                stack=[],
                cls_name=None,
            ),
            context=normal_error,  # normal error untouched
        ),
    )

    # Test depth 2
    assert truncate_serialized_error(
        error, field_size_limit=150, max_depth=2
    ) == SerializableErrorInfo(
        message="M" * 150 + " (TRUNCATED)",
        stack=["A" * 60, "B" * 60, "(TRUNCATED)"],
        cls_name="MyClassName",
        cause=SerializableErrorInfo(
            message="M" * 150 + " (TRUNCATED)",
            stack=["F" * 60, "G" * 60, "(TRUNCATED)"],
            cls_name=None,
            cause=None,
            context=None,
        ),
        context=SerializableErrorInfo(
            message="J" * 150 + " (TRUNCATED)",
            stack=["K" * 60, "L" * 60, "(TRUNCATED)"],
            cls_name=None,
            cause=SerializableErrorInfo(
                message="M" * 150 + " (TRUNCATED)",
                stack=["F" * 60, "G" * 60, "(TRUNCATED)"],
                cls_name=None,
                cause=None,
                context=None,
            ),
            context=normal_error,  # normal error untouched
        ),
    )

    assert truncate_serialized_error(error, field_size_limit=10000, max_depth=0) == error

    # verify class name truncation
    assert (
        truncate_serialized_error(error._replace(cls_name="A" * 1001), 10000, max_depth=0).cls_name
        == "A" * 1000 + " (TRUNCATED)"
    )
