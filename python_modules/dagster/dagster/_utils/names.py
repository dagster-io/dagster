import re


def clean_asset_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name by replacing invalid characters with underscores."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)
