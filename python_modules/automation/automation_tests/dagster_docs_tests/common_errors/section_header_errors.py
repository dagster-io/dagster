"""Docstring fixtures for testing section header errors."""

from dagster._annotations import public


@public
class SectionHeaderErrorFixtures:
    """Fixtures for testing section header error detection."""

    @public
    def incorrect_capitalization(self, param1, param2):
        """Function with incorrect section capitalization.

        args:  # Should be "Args:"
            param1: Description of param1
            param2: Description of param2

        returns:  # Should be "Returns:"
            Description of return value
        """
        pass

    @public
    def missing_colons(self, param1):
        """Function with missing colons in section headers.

        Args  # Missing colon
            param1: Description of param1

        Returns  # Missing colon
            Description of return value
        """
        pass

    @public
    def incorrect_section_names(self, param1):
        """Function with incorrect section names.

        Parameters:  # Should be "Args:"
            param1: Description of param1

        Return:  # Should be "Returns:"
            Description of return value

        Raise:  # Should be "Raises:"
            ValueError: When something goes wrong
        """
        pass

    @public
    def double_colon_headers(self, param1):
        """Function with double colon section headers.

        Args::  # Extra colon
            param1: Description of param1

        Returns::  # Extra colon
            Description of return value
        """
        pass
