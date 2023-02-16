from dagster_test_package.version import __version__


def test_version():
    assert __version__
