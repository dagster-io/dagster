import pytest

from dagster_test.utils.docstring_comparison import compare_docstring_parameters


def test_compare_docstring_parameters_with_itself():
    """Test compare_docstring_parameters using itself as an argument."""
    result = compare_docstring_parameters(compare_docstring_parameters)
    
    # The function should have no issues when comparing itself
    # since its docstring should match its signature
    assert not result.has_issues(), (
        f"compare_docstring_parameters failed self-analysis:\n"
        f"Missing parameters: {result.missing_parameters}\n"
        f"Extra parameters: {result.extra_parameters}\n"
        f"Type mismatches: {result.type_mismatches}\n"
        f"Missing return info: {result.missing_return_info}\n"
        f"Return type mismatch: {result.return_type_mismatch}"
    )
    
    # Specifically check that no discrepancies were found
    assert result.missing_parameters == []
    assert result.extra_parameters == []
    assert result.type_mismatches == []
    assert result.missing_return_info is False
    assert result.return_type_mismatch is None


def test_function_with_missing_docstring_params():
    """Test with a function that has parameters missing from docstring."""
    def func_missing_params(a: int, b: str) -> bool:
        """Function with incomplete docstring.
        
        Args:
            a: First parameter
            
        Returns:
            bool: Some boolean value
        """
        return True
    
    result = compare_docstring_parameters(func_missing_params)
    
    assert result.has_issues()
    assert 'b' in result.missing_parameters
    assert 'a' not in result.missing_parameters


def test_function_with_extra_docstring_params():
    """Test with a function that has extra parameters in docstring."""
    def func_extra_params(a: int) -> bool:
        """Function with extra docstring parameters.
        
        Args:
            a: First parameter
            b: This parameter doesn't exist in signature
            
        Returns:
            bool: Some boolean value
        """
        return True
    
    result = compare_docstring_parameters(func_extra_params)
    
    assert result.has_issues()
    assert 'b' in result.extra_parameters
    assert 'a' not in result.extra_parameters


def test_function_with_type_mismatches():
    """Test with a function that has type mismatches."""
    def func_type_mismatch(a: int) -> bool:
        """Function with type mismatches.
        
        Args:
            a (str): This should be int, not str
            
        Returns:
            str: This should be bool, not str
        """
        return True
    
    result = compare_docstring_parameters(func_type_mismatch)
    
    assert result.has_issues()
    assert len(result.type_mismatches) == 1
    assert result.type_mismatches[0]['parameter'] == 'a'
    assert result.type_mismatches[0]['signature_type'] == 'int'
    assert result.type_mismatches[0]['docstring_type'] == 'str'
    assert result.return_type_mismatch is not None
    assert result.return_type_mismatch['signature_type'] == 'bool'
    assert result.return_type_mismatch['docstring_type'] == 'str'


def test_function_with_no_docstring():
    """Test with a function that has no docstring."""
    def func_no_docstring(a: int, b: str) -> bool:
        return True
    
    result = compare_docstring_parameters(func_no_docstring)
    
    assert result.has_issues()
    assert set(result.missing_parameters) == {'a', 'b'}
    assert result.missing_return_info is True


def test_function_with_perfect_docstring():
    """Test with a function that has a perfect docstring."""
    def func_perfect(a: int, b: str) -> bool:
        """Function with perfect docstring.
        
        Args:
            a (int): First parameter
            b (str): Second parameter
            
        Returns:
            bool: Some boolean value
        """
        return True
    
    result = compare_docstring_parameters(func_perfect)
    
    assert not result.has_issues()
    assert result.missing_parameters == []
    assert result.extra_parameters == []
    assert result.type_mismatches == []
    assert result.missing_return_info is False
    assert result.return_type_mismatch is None