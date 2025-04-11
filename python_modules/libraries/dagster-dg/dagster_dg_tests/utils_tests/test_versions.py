from unittest import mock

from dagster_dg.utils.version import get_uv_tool_core_pin_string


def test_get_uv_tool_core_pin_string():
    assert get_uv_tool_core_pin_string() == ""

    with mock.patch("dagster_dg.utils.version.__version__", "0.26.3"):
        assert get_uv_tool_core_pin_string() == "==1.10.3"
