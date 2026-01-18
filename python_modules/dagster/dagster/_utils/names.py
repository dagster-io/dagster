import re


def clean_name(name: str) -> str:
    """Cleans an input to be a valid Dagster name by replacing invalid characters with underscores."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


def clean_name_lower(name: str) -> str:
    """Cleans an input to be a valid Dagster name by replacing invalid characters with underscores
    and converting uppercase characters into lowercase characters.
    """
    return clean_name(name=name).lower()


def clean_name_lower_with_dots(name: str) -> str:
    """Cleans an input to be a valid Dagster name by replacing invalid characters with underscores
    and converting uppercase characters into lowercase characters. This function keeps dots from the original string.
    """
    return re.sub(r"[^A-Za-z0-9_.]+", "_", name).lower()
