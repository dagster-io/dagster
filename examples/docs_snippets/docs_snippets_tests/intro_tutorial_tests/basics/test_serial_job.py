from docs_snippets.intro_tutorial.basics.connecting_ops.serial_job import serial


def test_serial_graph():
    result = serial.execute_in_process()
    assert result.success
