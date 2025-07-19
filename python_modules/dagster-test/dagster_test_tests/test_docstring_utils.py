"""Tests for docstring utilities."""

from dagster_test.docstring_utils import compare_docstring_parameters


def test_compare_docstring_parameters_complete_match():
    """Test function where docstring parameters match function parameters exactly."""
    def example_func(a: int, b: str):
        """Example function.
        
        Args:
            a: First parameter
            b: Second parameter
        """
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == set()
    assert result.extra_in_docstring == set()
    assert result.function_parameters == {"a", "b"}
    assert result.docstring_parameters == {"a", "b"}


def test_compare_docstring_parameters_missing_from_docstring():
    """Test function with parameters missing from docstring."""
    def example_func(a: int, b: str, c: float = 1.0):
        """Example function.
        
        Args:
            a: First parameter
            b: Second parameter
        """
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == {"c"}
    assert result.extra_in_docstring == set()
    assert result.function_parameters == {"a", "b", "c"}
    assert result.docstring_parameters == {"a", "b"}


def test_compare_docstring_parameters_extra_in_docstring():
    """Test function with extra parameters in docstring."""
    def example_func(a: int, b: str):
        """Example function.
        
        Args:
            a: First parameter
            b: Second parameter
            d: This parameter doesn't exist in function signature
        """
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == set()
    assert result.extra_in_docstring == {"d"}
    assert result.function_parameters == {"a", "b"}
    assert result.docstring_parameters == {"a", "b", "d"}


def test_compare_docstring_parameters_both_missing_and_extra():
    """Test function with both missing and extra parameters."""
    def example_func(a: int, b: str, c: float):
        """Example function.
        
        Args:
            a: First parameter
            d: This parameter doesn't exist in function signature
        """
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == {"b", "c"}
    assert result.extra_in_docstring == {"d"}
    assert result.function_parameters == {"a", "b", "c"}
    assert result.docstring_parameters == {"a", "d"}


def test_compare_docstring_parameters_no_docstring():
    """Test function with no docstring."""
    def example_func(a: int, b: str):
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == {"a", "b"}
    assert result.extra_in_docstring == set()
    assert result.function_parameters == {"a", "b"}
    assert result.docstring_parameters == set()


def test_compare_docstring_parameters_empty_docstring():
    """Test function with empty docstring."""
    def example_func(a: int, b: str):
        """"""
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == {"a", "b"}
    assert result.extra_in_docstring == set()
    assert result.function_parameters == {"a", "b"}
    assert result.docstring_parameters == set()


def test_compare_docstring_parameters_no_parameters():
    """Test function with no parameters."""
    def example_func():
        """Example function with no parameters."""
        pass
    
    result = compare_docstring_parameters(example_func)
    assert result.missing_from_docstring == set()
    assert result.extra_in_docstring == set()
    assert result.function_parameters == set()
    assert result.docstring_parameters == set()