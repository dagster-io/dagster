from dagster import Out
from dagster._core.definitions.output import DEFAULT_IO_MANAGER_KEY


def test_output_definition():
    out_onlyreq = Out(is_required=True)
    assert out_onlyreq.optional is False

    out_none = Out()
    assert out_none.optional is False
    assert out_none.io_manager_key == DEFAULT_IO_MANAGER_KEY
