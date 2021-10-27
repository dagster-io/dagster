from docs_snippets.intro_tutorial.basics.connecting_solids.serial_pipeline import serial
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_serial_graph():
    result = serial.execute_in_process()
    assert result.success
