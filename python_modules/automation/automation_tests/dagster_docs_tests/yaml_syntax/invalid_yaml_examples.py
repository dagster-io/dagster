"""Docstring fixtures with invalid YAML code blocks."""

from dagster._annotations import public


@public
class InvalidYAMLFixtures:
    """Fixtures for testing invalid YAML syntax detection."""

    @public
    def yaml_with_indentation_error(self):
        """Example with YAML indentation error.

        Examples:
            Invalid YAML - incorrect indentation:

            .. code-block:: yaml

                database:
                  host: localhost
                port: 5432  # This should be indented
                  name: mydb
        """
        pass

    @public
    def yaml_with_missing_colon(self):
        """Example with YAML missing colon.

        Examples:
            Invalid YAML - missing colon:

            .. code-block:: yaml

                database
                  host: localhost
                  port: 5432
        """
        pass

    @public
    def yaml_with_unmatched_brackets(self):
        """Example with YAML unmatched brackets.

        Examples:
            Invalid YAML - unmatched brackets:

            .. code-block:: yaml

                config:
                  items: [item1, item2, item3
                  other: value
        """
        pass

    @public
    def yaml_with_invalid_multiline(self):
        """Example with invalid YAML multiline structure.

        Examples:
            Invalid YAML - incomplete multiline:

            .. code-block:: yaml

                description: |
                  This is a multiline string
                  that spans multiple lines
                # Missing closing or continuation
                other_field: value
        """
        pass
