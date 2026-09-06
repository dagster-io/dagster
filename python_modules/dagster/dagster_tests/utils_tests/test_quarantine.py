import pytest

pytest_plugins = ["pytester"]

TEST_FILE = """
    import pytest

    @pytest.mark.quarantined
    def test_quarantined_passing():
        assert True

    @pytest.mark.quarantined
    def test_quarantined_failing():
        assert False

    def test_normal_passing():
        assert True

    def test_normal_failing():
        assert False
"""


PLUGIN = "dagster._utils.test.quarantine"


def _run(pytester, monkeypatch, env_value, *extra_args):
    if env_value is None:
        monkeypatch.delenv("RUN_QUARANTINED", raising=False)
    else:
        monkeypatch.setenv("RUN_QUARANTINED", env_value)
    pytester.makepyfile(TEST_FILE)
    return pytester.runpytest_subprocess("-p", PLUGIN, *extra_args)


def test_unset_skips_quarantined(pytester, monkeypatch):
    result = _run(pytester, monkeypatch, None, "-v")
    result.assert_outcomes(passed=1, failed=1, skipped=2)
    result.stdout.fnmatch_lines(["*test_quarantined_passing*SKIPPED*"])
    result.stdout.fnmatch_lines(["*test_quarantined_failing*SKIPPED*"])


def test_env_var_inverts_selection(pytester, monkeypatch):
    result = _run(pytester, monkeypatch, "1", "-v")
    result.assert_outcomes(passed=1, failed=1, deselected=2)


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "Yes"])
def test_truthy_env_values(pytester, monkeypatch, value):
    result = _run(pytester, monkeypatch, value)
    result.assert_outcomes(passed=1, failed=1, deselected=2)


@pytest.mark.parametrize("value", ["", "0", "false", "no"])
def test_falsy_env_values(pytester, monkeypatch, value):
    result = _run(pytester, monkeypatch, value)
    result.assert_outcomes(passed=1, failed=1, skipped=2)


def test_marker_registered_strict(pytester, monkeypatch):
    monkeypatch.delenv("RUN_QUARANTINED", raising=False)
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.quarantined
        def test_marked():
            assert True
        """
    )
    result = pytester.runpytest_subprocess("-p", PLUGIN, "--strict-markers")
    result.assert_outcomes(skipped=1)
