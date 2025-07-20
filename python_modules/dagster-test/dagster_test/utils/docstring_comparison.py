import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Union

from docstring_parser import parse


class DocstringComparisonResult:
    """Contains information about discrepancies between function signature and docstring."""
    
    def __init__(self):
        self.missing_parameters: List[str] = []
        self.extra_parameters: List[str] = []
        self.type_mismatches: List[Dict[str, Any]] = []
        self.missing_return_info: bool = False
        self.return_type_mismatch: Optional[Dict[str, Any]] = None
    
    def has_issues(self) -> bool:
        """Returns True if any discrepancies were found."""
        return bool(
            self.missing_parameters or
            self.extra_parameters or
            self.type_mismatches or
            self.missing_return_info or
            self.return_type_mismatch
        )


def compare_docstring_parameters(func: Callable[..., Any]) -> DocstringComparisonResult:
    """Compare function signature with docstring parameters and return discrepancies.
    
    Args:
        func: The function to analyze
        
    Returns:
        DocstringComparisonResult: Object containing information about discrepancies
    """
    result = DocstringComparisonResult()
    
    # Get function signature
    sig = inspect.signature(func)
    sig_params = {name: param for name, param in sig.parameters.items()}
    
    # Get return annotation
    return_annotation = sig.return_annotation
    
    # Parse docstring
    doc_str = func.__doc__
    if doc_str is None:
        # If no docstring, all parameters are missing from docs
        result.missing_parameters = list(sig_params.keys())
        if return_annotation != inspect.Signature.empty:
            result.missing_return_info = True
        return result
    
    try:
        docstring = parse(doc_str)
    except Exception:
        # If docstring can't be parsed, treat as missing
        result.missing_parameters = list(sig_params.keys())
        if return_annotation != inspect.Signature.empty:
            result.missing_return_info = True
        return result
    
    # Get docstring parameters
    doc_params = {p.arg_name: p for p in docstring.params}
    
    # Find missing parameters (in signature but not in docstring)
    sig_param_names = set(sig_params.keys())
    doc_param_names = set(doc_params.keys())
    
    result.missing_parameters = list(sig_param_names - doc_param_names)
    result.extra_parameters = list(doc_param_names - sig_param_names)
    
    # Check type mismatches for common parameters
    common_params = sig_param_names & doc_param_names
    for param_name in common_params:
        sig_param = sig_params[param_name]
        doc_param = doc_params[param_name]
        
        # Compare types if both are specified
        if (sig_param.annotation != inspect.Parameter.empty and 
            doc_param.type_name is not None):
            
            sig_type_str = _get_type_string(sig_param.annotation)
            doc_type_str = doc_param.type_name.strip()
            
            if sig_type_str != doc_type_str:
                result.type_mismatches.append({
                    'parameter': param_name,
                    'signature_type': sig_type_str,
                    'docstring_type': doc_type_str
                })
    
    # Check return type
    if return_annotation != inspect.Signature.empty:
        if docstring.returns is None:
            result.missing_return_info = True
        elif docstring.returns.type_name is not None:
            sig_return_type = _get_type_string(return_annotation)
            doc_return_type = docstring.returns.type_name.strip()
            
            if sig_return_type != doc_return_type:
                result.return_type_mismatch = {
                    'signature_type': sig_return_type,
                    'docstring_type': doc_return_type
                }
    
    return result


def _get_type_string(annotation: Any) -> str:
    """Convert a type annotation to a string representation."""
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    elif hasattr(annotation, '_name'):
        # Handle typing generics like Optional, List, etc.
        return str(annotation)
    else:
        return str(annotation)