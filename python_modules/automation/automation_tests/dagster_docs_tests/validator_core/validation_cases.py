"""Docstring fixtures for testing core validator functionality."""

from dagster._annotations import public


@public
class BasicValidationFixtures:
    """Fixtures for testing basic validator functionality."""

    def simple_valid_docstring(self):
        """This is a simple docstring."""
        pass

    @public
    def google_style_docstring(self, param1, param2):
        """Function with Google-style docstring.

        Args:
            param1: Description of param1
            param2: Description of param2

        Returns:
            Description of return value

        Examples:
            >>> example_call()
            'result'
        """
        pass

    @public
    def malformed_section_header(self, param1):
        """Function with malformed section header.

        arguments:  # Should be "Args:"
            param1: Description
        """
        pass

    @public
    def sphinx_role_usage(self):
        """Function using Sphinx roles.

        See :py:class:`SomeClass` and :func:`some_function`.
        """
        pass


@public
class EdgeCaseFixtures:
    """Fixtures for testing edge cases and false positive prevention."""

    @public
    def words_ending_with_period(self, output_required):
        """Function that explains return behavior.

        Args:
            output_required: Whether the function will always materialize an asset.
                If False, the function can conditionally not yield a result.
                Note that you must use yield rather than return. return will not respect
                this setting and will always produce an asset materialization, even if None is
                returned.
        """
        pass

    @public
    def dagster_asset_specific_case(self, output_required):
        """Function with similar pattern to dagster.asset.

        Args:
            output_required: Whether the function will always materialize an asset.
                Defaults to True. If False, the function can conditionally not yield a result.
                If no result is yielded, no output will be materialized to storage and downstream
                assets will not be materialized. Note that for output_required to work at all, you
                must use yield in your asset logic rather than return. return will not respect
                this setting and will always produce an asset materialization, even if None is
                returned.
        """
        pass
