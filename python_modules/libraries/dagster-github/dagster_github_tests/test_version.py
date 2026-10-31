from dagster_github.version import __version__


def test_version():
    assert __version__  # ty: ignore[redundant-condition]
