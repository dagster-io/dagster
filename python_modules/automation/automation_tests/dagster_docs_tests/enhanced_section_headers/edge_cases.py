"""Docstring fixtures for testing edge cases."""

from dagster._annotations import public


@public
class EdgeCasesFixtures:
    """Fixtures for testing edge cases and boundary conditions."""

    @public
    def headers_within_code_blocks(self, param1):
        """Function with code examples containing headers.

        Args:
            param1: Description

        Examples:
            Example showing docstring format:

            .. code-block:: python

                '''
                Args:
                    example_param: This is in a code example
                '''
        """
        pass

    @public
    def template_var_attributes_example(self):
        """Template variable decorator function.

        This decorator marks functions for use in YAML templates.

        Examples:
            Basic usage in YAML:

            .. code-block:: yaml

                type: my_project.components.DataProcessor
                template_vars_module: .template_vars
                attributes:
                  database_url: "{{ database_url }}"
                  table_name: "{{ component_specific_table }}"

            Component class usage:

            .. code-block:: yaml

                type: my_project.components.MyComponent
                attributes:
                  config: "{{ default_config }}"
                  name: "{{ context_aware_value }}"

        Args:
            fn: The function to decorate as a template variable.

        Returns:
            The decorated function with template variable metadata.
        """
        pass

    @public
    def see_also_cross_references(self):
        """See Also section with cross-references.

        See Also:
            - :py:class:`dagster.ComponentLoadContext`: Context object available to template variables
        """
        pass

    @public
    def code_block_enhancement_test(self):
        """Function that tests code block enhancement capability.

        Examples:
            This function demonstrates usage:

            >>> example_function()
            'result'
        """
        pass
