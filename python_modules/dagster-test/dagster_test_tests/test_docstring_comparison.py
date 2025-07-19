import pytest
from dagster_test.utils.docstring_comparison import compare_docstring_parameters


def test_compare_docstring_parameters_on_itself():
    """Test the compare_docstring_parameters function by analyzing itself."""
    result = compare_docstring_parameters(compare_docstring_parameters)
    
    # The function should have proper documentation, so we expect minimal issues
    print(f"Missing parameters: {result.missing_parameters}")
    print(f"Extra parameters: {result.extra_parameters}")
    print(f"Type mismatches: {[m.parameter_name for m in result.type_mismatches]}")
    print(f"Return type mismatch: {result.return_type_mismatch}")
    print(f"Signature return type: {result.signature_return_type}")
    print(f"Docstring return type: {result.docstring_return_type}")
    
    # Print detailed issues for debugging
    for issue in result.all_issues:
        print(f"Issue: {issue.issue_type} - {issue.parameter_name}: {issue.description}")
    
    # Basic validation - the function should be well-documented
    # We expect the function to be documented properly, but let's be flexible
    assert isinstance(result.missing_parameters, list)
    assert isinstance(result.extra_parameters, list)
    assert isinstance(result.type_mismatches, list)
    assert isinstance(result.return_type_mismatch, bool)
    
    # The function should have a func parameter documented
    assert "func" not in result.missing_parameters, "The 'func' parameter should be documented in the docstring"
    
    # There should be no extra parameters in the docstring
    assert len(result.extra_parameters) == 0, f"Found extra parameters in docstring: {result.extra_parameters}"


def test_compare_docstring_parameters_with_mismatches():
    """Test the function with a function that has intentional docstring mismatches."""
    
    def example_func(x: int, y: str = "default") -> bool:
        """Example function with intentional docstring issues.
        
        Args:
            x: An integer parameter
            z: A parameter that doesn't exist in signature
            y: A string parameter (but documented as int)
                
        Returns:
            str: Return type that doesn't match signature
        """
        return x > 0
    
    result = compare_docstring_parameters(example_func)
    
    # Should find the missing 'y' parameter issue has been resolved since y is documented
    # Should find 'z' as extra parameter
    assert "z" in result.extra_parameters
    
    # Should find return type mismatch
    assert result.return_type_mismatch is True
    assert result.signature_return_type == "bool"
    assert result.docstring_return_type == "str"
    
    # Should have multiple issues
    assert len(result.all_issues) >= 2  # At least extra param and return type mismatch


def test_compare_docstring_parameters_no_docstring():
    """Test the function with a function that has no docstring."""
    
    def no_doc_func(a: int, b: str) -> None:
        pass
    
    result = compare_docstring_parameters(no_doc_func)
    
    # Should find all parameters as missing from docstring
    assert "a" in result.missing_parameters
    assert "b" in result.missing_parameters
    assert len(result.extra_parameters) == 0
    assert len(result.type_mismatches) == 0


def test_compare_docstring_parameters_perfect_match():
    """Test the function with a perfectly documented function."""
    
    def perfect_func(x: int, y: str = "test") -> bool:
        """A perfectly documented function.
        
        Args:
            x (int): An integer parameter
            y (str): A string parameter with default value
            
        Returns:
            bool: A boolean result
        """
        return x > 0
    
    result = compare_docstring_parameters(perfect_func)
    
    # Should have no issues
    assert len(result.missing_parameters) == 0
    assert len(result.extra_parameters) == 0
    assert len(result.type_mismatches) == 0
    assert result.return_type_mismatch is False
    assert len(result.all_issues) == 0