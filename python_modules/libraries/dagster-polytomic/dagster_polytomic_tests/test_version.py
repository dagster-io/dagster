from dagster_polytomic.version import __version__


def test_version():
    assert __version__  # ty: ignore[redundant-condition]
