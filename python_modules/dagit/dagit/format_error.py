from typing import Any, Dict

from graphql.error.base import GraphQLError
from six import text_type

from dagster.utils.log import get_stack_trace_array


# based on default_format_error copied and pasted from graphql_server 1.1.1
def format_error_with_stack_trace(error):

    # type: (Exception) -> Dict[str, Any]

    formatted_error = {'message': text_type(error)}  # type: Dict[str, Any]
    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error['locations'] = [
                {'line': loc.line, 'column': loc.column} for loc in error.locations
            ]
        if error.path is not None:
            formatted_error['path'] = error.path

        # this is what is different about this implementation
        # we print out stack traces to ease debugging
        if hasattr(error, 'original_error') and error.original_error:
            formatted_error['stack_trace'] = get_stack_trace_array(error.original_error)
    else:
        formatted_error['stack_trace'] = get_stack_trace_array(error)

    return formatted_error
