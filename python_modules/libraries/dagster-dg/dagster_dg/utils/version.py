from dagster_shared.libraries import core_version_from_library_version

from dagster_dg.version import __version__


def get_uv_tool_core_pin_string() -> str:
    if __version__ == "1!0+dev":
        return ""
    else:
        return f"=={core_version_from_library_version(__version__)}"
