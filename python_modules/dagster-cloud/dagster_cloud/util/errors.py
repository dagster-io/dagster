from collections.abc import Sequence

from dagster._utils.error import SerializableErrorInfo

DAGSTER_FRAMEWORK_SUBSTRINGS = [
    "/site-packages/dagster/",
    "/python_modules/dagster/dagster",
]


def remove_dagster_framework_lines_from_serializable_exc_info(error_info: SerializableErrorInfo):
    return error_info._replace(
        stack=remove_dagster_framework_lines_from_stack_trace(error_info.stack),
        cause=(
            remove_dagster_framework_lines_from_serializable_exc_info(error_info.cause)
            if error_info.cause
            else None
        ),
        context=(
            remove_dagster_framework_lines_from_serializable_exc_info(error_info.context)
            if error_info.context
            else None
        ),
    )


def remove_dagster_framework_lines_from_stack_trace(
    stack: Sequence[str],
) -> Sequence[str]:
    # Remove lines until you find the first non-dagster framework line

    for i in range(len(stack)):
        if not _line_contains_dagster_framework_file(stack[i]):
            return stack[i:]

    # Return the full stack trace if its all Dagster framework lines,
    # to not be left with an empty stack trace
    return stack


def _line_contains_dagster_framework_file(line: str):
    # stack trace line starts with something like
    # File "/usr/local/lib/python3.11/site-packages/dagster/_core/execution/plan/utils.py",
    split_by_comma = line.split(",")
    if not split_by_comma:
        return False

    file_portion = split_by_comma[0]
    return any(
        framework_substring in file_portion for framework_substring in DAGSTER_FRAMEWORK_SUBSTRINGS
    )
