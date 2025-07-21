from dagster_test.utils.docstring_comparison import compare_docstring_parameters


def test_compare_docstring_parameters_on_itself():
    """Test that compare_docstring_parameters works correctly when analyzing itself."""
    # Run the function on itself
    result = compare_docstring_parameters(compare_docstring_parameters)

    # The function should have no issues since it's properly documented
    assert not result.has_issues, f"Function has issues: {result.mismatches}"
    assert len(result.mismatches) == 0
    assert result.return_type_mismatch is None


def test_function_with_missing_docstring_param():
    """Test detecting missing parameters in docstring."""

    def example_func(param1: str, param2: int) -> bool:
        """Function with incomplete docstring.

        Args:
            param1 (str): First parameter

        Returns:
            bool: Some boolean value
        """
        return True

    result = compare_docstring_parameters(example_func)

    assert result.has_issues
    assert len(result.mismatches) == 1
    assert result.mismatches[0].name == "param2"
    assert result.mismatches[0].issue_type == "missing_in_docstring"
    assert result.mismatches[0].function_type == "int"


def test_function_with_extra_docstring_param():
    """Test detecting extra parameters in docstring."""

    def example_func(param1: str) -> bool:
        """Function with extra parameter in docstring.

        Args:
            param1: First parameter
            param2: This parameter doesn't exist in function

        Returns:
            bool: Some boolean value
        """
        return True

    result = compare_docstring_parameters(example_func)

    assert result.has_issues
    assert len(result.mismatches) == 1
    assert result.mismatches[0].name == "param2"
    assert result.mismatches[0].issue_type == "extra_in_docstring"


def test_function_with_type_mismatch():
    """Test detecting type mismatches."""

    def example_func(param1: str) -> bool:
        """Function with type mismatch.

        Args:
            param1 (int): This should be str, not int

        Returns:
            bool: Some boolean value
        """
        return True

    result = compare_docstring_parameters(example_func)

    assert result.has_issues
    assert len(result.mismatches) == 1
    assert result.mismatches[0].name == "param1"
    assert result.mismatches[0].issue_type == "type_mismatch"
    assert result.mismatches[0].function_type == "str"
    assert result.mismatches[0].docstring_type == "int"


def test_function_with_no_docstring():
    """Test function with no docstring."""

    def example_func(param1: str, param2: int) -> bool:
        return True

    result = compare_docstring_parameters(example_func)

    assert result.has_issues
    assert len(result.mismatches) == 2  # Both parameters missing from docstring
    param_names = {mismatch.name for mismatch in result.mismatches}
    assert param_names == {"param1", "param2"}
    for mismatch in result.mismatches:
        assert mismatch.issue_type == "missing_in_docstring"


def test_function_with_return_type_mismatch():
    """Test detecting return type mismatches."""

    def example_func() -> str:
        """Function with return type mismatch.

        Returns:
            int: Should be str, not int
        """
        return "test"

    result = compare_docstring_parameters(example_func)

    assert result.has_issues
    assert result.return_type_mismatch is not None
    assert result.return_type_mismatch.name == "return"
    assert result.return_type_mismatch.issue_type == "type_mismatch"
    assert result.return_type_mismatch.function_type == "str"
    assert result.return_type_mismatch.docstring_type == "int"


def test_perfect_function():
    """Test function with perfect docstring."""

    def example_func(param1: str, param2: int) -> bool:
        """Function with perfect docstring.

        Args:
            param1 (str): First parameter
            param2 (int): Second parameter

        Returns:
            bool: Some boolean value
        """
        return True

    result = compare_docstring_parameters(example_func)

    assert not result.has_issues
    assert len(result.mismatches) == 0
    assert result.return_type_mismatch is None
