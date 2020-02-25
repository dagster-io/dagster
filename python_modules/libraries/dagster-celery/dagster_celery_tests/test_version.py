def test_version():
    from dagster_celery.version import __version__

    assert __version__
