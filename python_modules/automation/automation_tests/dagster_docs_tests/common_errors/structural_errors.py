"""Docstring fixtures for testing structural errors."""

from dagster._annotations import public


@public
class StructuralErrorFixtures:
    """Fixtures for testing structural error detection."""

    @public
    def empty_sections(self):
        """Function with empty sections.

        Args:
            # Empty section - no parameters listed

        Returns:
            # Another empty section

        Raises:
            # Yet another empty section
        """
        pass

    @public
    def duplicate_sections(self, param1, param2):
        """Function with duplicate sections.

        Args:
            param1: First parameter

        Args:
            param2: Duplicate Args section

        Returns:
            First return description

        Returns:
            Duplicate Returns section
        """
        pass

    @public
    def sections_in_wrong_order(self, param1):
        """Function with sections in unusual order.

        Returns:
            Return value described before Args

        Raises:
            Exception described before Args

        Args:
            param1: Parameter described last

        Examples:
            Example shown at the end
        """
        pass
