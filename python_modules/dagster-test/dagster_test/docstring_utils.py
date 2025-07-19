"""Utilities for inspecting and validating docstrings."""

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Optional, Set

from docstring_parser import parse as parse_docstring


@dataclass
class DocstringParameterComparison:
    """Result of comparing function parameters with docstring parameters.
    
    Args:
        missing_from_docstring: Parameter names that exist in the function signature
            but are not documented in the docstring.
        extra_in_docstring: Parameter names that are documented in the docstring
            but don't exist in the function signature.
        function_parameters: Set of all parameter names from the function signature.
        docstring_parameters: Set of all parameter names from the docstring.
    """
    missing_from_docstring: Set[str]
    extra_in_docstring: Set[str]
    function_parameters: Set[str]
    docstring_parameters: Set[str]


def compare_docstring_parameters(func: Callable[..., Any]) -> DocstringParameterComparison:
    """Compare function parameters with docstring parameters.
    
    This function analyzes a function's signature and docstring to identify:
    - Parameters that exist in the function but aren't documented
    - Parameters that are documented but don't exist in the function
    
    Args:
        func: The function to analyze.
        
    Returns:
        DocstringParameterComparison containing sets of missing and extra parameters.
        
    Example:
        >>> def example_func(a: int, b: str, c: float = 1.0):
        ...     '''Example function.
        ...     
        ...     Args:
        ...         a: First parameter
        ...         b: Second parameter
        ...         d: This parameter doesn't exist in function signature
        ...     '''
        ...     pass
        >>> result = compare_docstring_parameters(example_func)
        >>> result.missing_from_docstring
        {'c'}
        >>> result.extra_in_docstring  
        {'d'}
    """
    # Get function signature and extract parameter names
    sig = inspect.signature(func)
    function_parameters = set(sig.parameters.keys())
    
    # Parse docstring to get documented parameters
    docstring_parameters: Set[str] = set()
    doc_str = func.__doc__
    
    if doc_str:
        try:
            parsed_docstring = parse_docstring(doc_str)
            docstring_parameters = {param.arg_name for param in parsed_docstring.params if param.arg_name}
        except Exception:
            # If parsing fails, assume no documented parameters
            pass
    
    # Calculate differences
    missing_from_docstring = function_parameters - docstring_parameters
    extra_in_docstring = docstring_parameters - function_parameters
    
    return DocstringParameterComparison(
        missing_from_docstring=missing_from_docstring,
        extra_in_docstring=extra_in_docstring,
        function_parameters=function_parameters,
        docstring_parameters=docstring_parameters,
    )