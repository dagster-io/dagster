"""Docstring fixtures for testing RST syntax errors."""

from dagster._annotations import public


@public
class RSTSyntaxErrorFixtures:
    """Fixtures for testing RST syntax error detection."""

    @public
    def malformed_code_blocks(self):
        """Function with malformed code blocks.

        Example:
            .. code-block: python  # Missing double colon

                def example():
                    return "hello"
        """
        pass

    @public
    def misspelled_directive_name(self):
        """Function with misspelled directive name.

        Example:
            .. code-kjdfkdblock:: python  # Correct :: but misspelled directive

                def example():
                    return "hello"
        """
        pass

    @public
    def unmatched_backticks(self, param1):
        """Function with unmatched backticks.

        This function uses `unmatched backtick and `another unmatched backtick.
        Also has ``double backtick but only one closing backtick`.

        Args:
            param1: A parameter with `unmatched backtick in description

        Returns:
            A value with ``unmatched double backticks
        """
        pass

    @public
    def malformed_lists(self, param1):
        """Function with malformed lists.

        This function does several things:

        - First item
        * Mixed bullet styles (should be consistent)
        - Third item
          - Nested item with wrong indentation
        - Item with
        continuation on wrong line

        Args:
            param1: Parameter description

        Returns:
            Description of return value
        """
        pass

    @public
    def malformed_links(self, param1):
        """Function with malformed links.

        See `malformed link <http://example.com` (missing closing angle bracket)
        Also see `another bad link <>`_ (empty URL)
        And `link with spaces in name but no underscore <http://example.com>`

        Args:
            param1: Parameter description

        Returns:
            Description of return value
        """
        pass
