"""Docstring fixtures for testing known valid Dagster symbol patterns.

This module contains representative examples of docstring patterns found in
actual Dagster public symbols that should validate successfully.
"""

from dagster._annotations import public


@public
class DagsterSymbolPatterns:
    """Representative patterns from actual Dagster public symbols."""

    @public
    def asset_with_examples(self, context, upstream_table):
        """Create an asset that depends on upstream data.

        This asset demonstrates common patterns found in Dagster public symbols.

        Args:
            context: The asset execution context
            upstream_table: Input data from upstream asset

        Returns:
            Processed data ready for downstream consumption

        Examples:
            Basic asset definition:

            .. code-block:: python

                @asset
                def my_asset(context, upstream_table):
                    return upstream_table.process()

        Note:
            This is a representative pattern based on actual Dagster symbols.
        """
        pass

    @public
    def config_with_metadata(self, config_value):
        """Configure with metadata patterns.

        Args:
            config_value: Configuration dictionary containing:
                - param1: First configuration parameter
                - param2: Second configuration parameter

        Returns:
            ConfiguredObject: Object configured with provided parameters

        Raises:
            ConfigError: If configuration is invalid
            ValidationError: If validation fails

        See Also:
            - :py:class:`dagster.Config`: Base configuration class
            - :py:func:`dagster.configured`: Configuration decorator
        """
        pass
