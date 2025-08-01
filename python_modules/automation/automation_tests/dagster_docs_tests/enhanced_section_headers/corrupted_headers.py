"""Docstring fixtures for testing corrupted section headers."""

from dagster._annotations import public


@public
class CorruptedHeaderCases:
    """Fixtures for testing corrupted section header detection."""

    @public
    def basic_corrupted_header(self, param1, param2):
        """Function with corrupted section header.

        Argsjdkfjdkjfdk:
        param1: Description of parameter
        param2: Another parameter

        Returns:
        Description of return value
        """
        pass

    @public
    def short_headers_not_flagged(self, param1):
        """Function with short text that shouldn't be flagged.

        A: This is just a short line with colon
        B: Another short line

        Args:
            param1: Real parameter
        """
        pass

    @public
    def multiple_colons_in_content(self, url_param, time_param):
        """Function with multiple colons in content.

        Args:
            url_param: URL like http://example.com:8080/path
            time_param: Time in format HH:MM:SS

        Returns:
            Dictionary with keys like {'status': 'success', 'time': '12:30:45'}
        """
        pass
