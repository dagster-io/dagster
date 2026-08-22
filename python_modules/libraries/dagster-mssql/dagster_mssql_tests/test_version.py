from dagster.version import __version__ as dagster_version
from dagster_mssql.version import __version__


def test_version():
    assert __version__ == dagster_version
