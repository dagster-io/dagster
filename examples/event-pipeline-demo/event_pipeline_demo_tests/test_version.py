from event_pipeline_demo.version import __version__


def test_version():
    assert isinstance(__version__, str)
    assert len(__version__.split('.')) == 3
    assert all((isinstance(int(num), int) for num in __version__.split('.')))
