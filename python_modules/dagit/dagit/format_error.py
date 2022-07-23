from typing import Dict

from graphql.error.base import GraphQLError

from dagster._utils.log import get_stack_trace_array


# based on default_format_error copied and pasted from graphql_server 1.1.1
def format_error_with_stack_trace(error: BaseException) -> Dict[str, object]:
    formatted_error: Dict[str, object] = {"message": str(error)}

    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error["locations"] = [
                {"line": loc.line, "column": loc.column} for loc in error.locations
            ]
        if error.path is not None:
            formatted_error["path"] = error.path

        # this is what is different about this implementation
        # we print out stack traces to ease debugging
        if hasattr(error, "original_error") and error.original_error:  # type: ignore [attr-defined]
            formatted_error["stack_trace"] = get_stack_trace_array(error.original_error)  # type: ignore [attr-defined]
    else:
        formatted_error["stack_trace"] = get_stack_trace_array(error)

    if hasattr(error, "__cause__") and error.__cause__:
        formatted_error["cause"] = format_error_with_stack_trace(error.__cause__)

    return formatted_error
