import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Union

from docstring_parser import parse


@dataclass
class ParameterMismatch:
    """Represents a mismatch between function signature and docstring parameters."""
    
    parameter_name: str
    issue_type: str
    signature_type: Optional[str] = None
    docstring_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class DocstringComparisonResult:
    """Result of comparing function signature with docstring parameters.
    
    Args:
        missing_parameters: Parameters in function signature but not in docstring
        extra_parameters: Parameters in docstring but not in function signature
        type_mismatches: Parameters with different types between signature and docstring
        return_type_mismatch: Whether return types differ between signature and docstring
        signature_return_type: Return type annotation from function signature
        docstring_return_type: Return type from docstring
        all_issues: List of all parameter mismatches found
    
    Returns:
        DocstringComparisonResult: Object containing all comparison results
    """
    
    missing_parameters: List[str]
    extra_parameters: List[str] 
    type_mismatches: List[ParameterMismatch]
    return_type_mismatch: bool
    signature_return_type: Optional[str]
    docstring_return_type: Optional[str]
    all_issues: List[ParameterMismatch]


def _get_type_string(annotation: Any) -> Optional[str]:
    """Convert a type annotation to a string representation."""
    if annotation is inspect.Parameter.empty:
        return None
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    return str(annotation)


def _normalize_type_string(type_str: Optional[str]) -> Optional[str]:
    """Normalize type strings for comparison."""
    if not type_str:
        return None
    
    # Handle common type variations
    normalized = type_str.replace("typing.", "").replace("<class '", "").replace("'>", "")
    normalized = normalized.replace("builtins.", "")
    
    # Handle Callable variations - treat them as equivalent
    if "Callable" in normalized:
        # Treat "Callable", "Callable[..., Any]", etc. as equivalent
        if "[" in normalized:
            # Keep the full signature for more specific matching
            pass
        else:
            # Just "Callable" - normalize to generic form
            normalized = "Callable"
    
    # Handle Union types
    if "Union[" in normalized:
        normalized = normalized.replace("Union[", "").replace("]", "")
        # Sort union components for consistent comparison
        if ", " in normalized:
            parts = [part.strip() for part in normalized.split(", ")]
            normalized = " | ".join(sorted(parts))
    
    return normalized


def compare_docstring_parameters(func: Callable[..., Any]) -> DocstringComparisonResult:
    """Compare function signature parameters with docstring parameters.
    
    Inspects a Python function for its parameter names, parameter types, and return type,
    then compares these against the parameters, parameter types, and return type encoded
    in the docstring. Returns detailed information about any discrepancies found.
    
    Args:
        func (Callable[..., Any]): The Python function to analyze
        
    Returns:
        DocstringComparisonResult: Object containing information about mismatches including
            missing parameters, extra parameters, type mismatches, and return type differences
    """
    # Get function signature
    sig = inspect.signature(func)
    signature_params = {name: param for name, param in sig.parameters.items()}
    
    # Get type hints
    type_hints = {}
    try:
        type_hints = func.__annotations__
    except AttributeError:
        pass
    
    # Parse docstring
    docstring = None
    if func.__doc__:
        try:
            docstring = parse(func.__doc__)
        except Exception:
            pass
    
    # Initialize result collections
    missing_parameters = []
    extra_parameters = []
    type_mismatches = []
    all_issues = []
    
    # Get docstring parameters
    docstring_params = {}
    if docstring and docstring.params:
        docstring_params = {param.arg_name: param for param in docstring.params}
    
    # Find missing parameters (in signature but not in docstring)
    signature_param_names = set(signature_params.keys())
    docstring_param_names = set(docstring_params.keys())
    
    missing = signature_param_names - docstring_param_names
    for param_name in missing:
        missing_parameters.append(param_name)
        issue = ParameterMismatch(
            parameter_name=param_name,
            issue_type="missing_from_docstring",
            description=f"Parameter '{param_name}' exists in function signature but not in docstring"
        )
        all_issues.append(issue)
    
    # Find extra parameters (in docstring but not in signature)
    extra = docstring_param_names - signature_param_names
    for param_name in extra:
        extra_parameters.append(param_name)
        issue = ParameterMismatch(
            parameter_name=param_name,
            issue_type="extra_in_docstring",
            description=f"Parameter '{param_name}' exists in docstring but not in function signature"
        )
        all_issues.append(issue)
    
    # Check type mismatches for common parameters
    common_params = signature_param_names & docstring_param_names
    for param_name in common_params:
        sig_param = signature_params[param_name]
        doc_param = docstring_params[param_name]
        
        # Get signature type
        sig_type = _get_type_string(sig_param.annotation)
        if not sig_type and param_name in type_hints:
            sig_type = _get_type_string(type_hints[param_name])
        
        # Get docstring type
        doc_type = doc_param.type_name if doc_param.type_name else None
        
        # Normalize for comparison
        normalized_sig_type = _normalize_type_string(sig_type)
        normalized_doc_type = _normalize_type_string(doc_type)
        
        # Check for mismatch - only report if both types exist and are genuinely different
        if (normalized_sig_type is not None and normalized_doc_type is not None 
            and normalized_sig_type != normalized_doc_type):
            # Special handling for Callable types
            if "Callable" in str(normalized_sig_type) and "Callable" in str(normalized_doc_type):
                # Both are callable types, consider them compatible
                pass
            else:
                mismatch = ParameterMismatch(
                    parameter_name=param_name,
                    issue_type="type_mismatch",
                    signature_type=sig_type,
                    docstring_type=doc_type,
                    description=f"Parameter '{param_name}' type mismatch: signature has '{sig_type}', docstring has '{doc_type}'"
                )
                type_mismatches.append(mismatch)
                all_issues.append(mismatch)
    
    # Check return type
    signature_return_type = _get_type_string(sig.return_annotation)
    if not signature_return_type and "return" in type_hints:
        signature_return_type = _get_type_string(type_hints["return"])
    
    docstring_return_type = None
    if docstring and docstring.returns and docstring.returns.type_name:
        docstring_return_type = docstring.returns.type_name
    
    # Normalize return types for comparison
    normalized_sig_return = _normalize_type_string(signature_return_type)
    normalized_doc_return = _normalize_type_string(docstring_return_type)
    
    return_type_mismatch = (
        normalized_sig_return != normalized_doc_return 
        and (normalized_sig_return is not None or normalized_doc_return is not None)
    )
    
    # Add return type mismatch to all_issues if it exists
    if return_type_mismatch:
        return_issue = ParameterMismatch(
            parameter_name="<return>",
            issue_type="return_type_mismatch",
            signature_type=signature_return_type,
            docstring_type=docstring_return_type,
            description=f"Return type mismatch: signature has '{signature_return_type}', docstring has '{docstring_return_type}'"
        )
        all_issues.append(return_issue)
    
    return DocstringComparisonResult(
        missing_parameters=missing_parameters,
        extra_parameters=extra_parameters,
        type_mismatches=type_mismatches,
        return_type_mismatch=return_type_mismatch,
        signature_return_type=signature_return_type,
        docstring_return_type=docstring_return_type,
        all_issues=all_issues
    )