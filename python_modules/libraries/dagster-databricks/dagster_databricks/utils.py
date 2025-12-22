import re


def snake_case(name: str) -> str:
    """Standard snake_case utility for Databricks components."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", str(name))
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower().strip("_")
