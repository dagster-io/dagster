# Normally we'd use dagster.seven for this, but we want to delay importing anything under the
# dagster package
try:
    from unittest import mock
except ImportError:
    # Because this dependency is not encoded setup.py deliberately
    # (we do not want to override or conflict with our users mocks)
    # we never fail when importing this.

    # This will only be used within *our* test environment of which
    # we have total control
    try:
        import mock
    except ImportError:
        pass


def test_no_warnings_on_import():
    with mock.patch('warnings.warn') as warn_mock:
        import dagster  # pylint: disable=unused-import

        expected_warnings = [
            'SOCKS support in urllib3 requires the installation of optional dependencies'
        ]
        for call in warn_mock.call_args_list:
            assert any(expected_warning in str(call) for expected_warning in expected_warnings)
