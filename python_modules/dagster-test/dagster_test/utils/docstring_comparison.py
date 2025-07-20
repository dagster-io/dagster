import inspect
from typing import Any, Optional, get_type_hints

from dagster_shared.record import record
from docstring_parser import parse


@record
class ParameterMismatch:
    """Represents a mismatch between function parameter and docstring parameter."""

    name: str
    issue_type: str  # "missing_in_docstring", "extra_in_docstring", "type_mismatch"
    function_type: Optional[str] = None
    docstring_type: Optional[str] = None
    description: Optional[str] = None


@record
class DocstringComparisonResult:
    """Result of comparing function signature with its docstring parameters."""

    mismatches: list[ParameterMismatch]
    return_type_mismatch: Optional[ParameterMismatch] = None

    @property
    def has_issues(self) -> bool:
        """Returns True if there are any parameter or return type mismatches."""
        return bool(self.mismatches or self.return_type_mismatch)


def compare_docstring_parameters(func: Any) -> DocstringComparisonResult:
    """Compare a Python function's signature with its docstring parameters.

    Inspects the function's parameters (names, types, return type) and compares them
    with the parameters documented in the docstring. Returns information about any
    mismatches found.

    Args:
        func: The Python function to analyze

    Returns:
        DocstringComparisonResult containing any mismatches found between the function
        signature and its docstring documentation
    """
    mismatches: list[ParameterMismatch] = []
    return_type_mismatch: Optional[ParameterMismatch] = None

    # Get function signature and type hints
    signature = inspect.signature(func)
    try:
        type_hints = get_type_hints(func)
    except (NameError, AttributeError):
        # Handle cases where type hints reference undefined types
        type_hints = {}

    # Parse docstring
    docstring = inspect.getdoc(func)
    if not docstring:
        # If no docstring, all parameters are missing from docstring
        for param_name in signature.parameters.keys():
            if param_name != "self":  # Skip 'self' parameter
                mismatches.append(
                    ParameterMismatch(
                        name=param_name,
                        issue_type="missing_in_docstring",
                        function_type=_format_type(type_hints.get(param_name)),
                    )
                )
        return DocstringComparisonResult(mismatches=mismatches)

    parsed_doc = parse(docstring)

    # Get function parameters (excluding 'self')
    func_params = {name: param for name, param in signature.parameters.items() if name != "self"}

    # Get docstring parameters
    doc_params = {param.arg_name: param for param in parsed_doc.params}

    # Find missing parameters in docstring
    for param_name in func_params.keys():
        if param_name not in doc_params:
            mismatches.append(
                ParameterMismatch(
                    name=param_name,
                    issue_type="missing_in_docstring",
                    function_type=_format_type(type_hints.get(param_name)),
                )
            )

    # Find extra parameters in docstring
    for param_name, doc_param in doc_params.items():
        if param_name not in func_params:
            mismatches.append(
                ParameterMismatch(
                    name=param_name,
                    issue_type="extra_in_docstring",
                    docstring_type=doc_param.type_name,
                    description=doc_param.description,
                )
            )

    # Check type mismatches for parameters that exist in both
    for param_name, doc_param in doc_params.items():
        if param_name in func_params and doc_param.type_name:
            func_type = type_hints.get(param_name)
            func_type_str = _format_type(func_type)
            doc_type_str = doc_param.type_name.strip()

            if func_type_str and doc_type_str and func_type_str != doc_type_str:
                # Simple string comparison - could be enhanced with more sophisticated type matching
                mismatches.append(
                    ParameterMismatch(
                        name=param_name,
                        issue_type="type_mismatch",
                        function_type=func_type_str,
                        docstring_type=doc_type_str,
                    )
                )

    # Check return type
    if parsed_doc.returns and parsed_doc.returns.type_name:
        func_return_type = type_hints.get("return")
        func_return_str = _format_type(func_return_type)
        doc_return_str = parsed_doc.returns.type_name.strip()

        if func_return_str and doc_return_str and func_return_str != doc_return_str:
            return_type_mismatch = ParameterMismatch(
                name="return",
                issue_type="type_mismatch",
                function_type=func_return_str,
                docstring_type=doc_return_str,
            )
    elif signature.return_annotation != inspect.Signature.empty and not parsed_doc.returns:
        return_type_mismatch = ParameterMismatch(
            name="return",
            issue_type="missing_in_docstring",
            function_type=_format_type(type_hints.get("return")),
        )
    elif parsed_doc.returns and signature.return_annotation == inspect.Signature.empty:
        return_type_mismatch = ParameterMismatch(
            name="return",
            issue_type="extra_in_docstring",
            docstring_type=parsed_doc.returns.type_name,
        )

    return DocstringComparisonResult(
        mismatches=mismatches, return_type_mismatch=return_type_mismatch
    )


def _format_type(type_annotation: Any) -> Optional[str]:
    """Format a type annotation as a string for comparison."""
    if type_annotation is None:
        return None

    # Handle basic types
    if hasattr(type_annotation, "__name__"):
        return type_annotation.__name__

    # Handle generic types and more complex annotations
    return str(type_annotation).replace("typing.", "")
