import re
import subprocess
import sys


def test_no_beta_warnings():
    process = subprocess.run(
        [sys.executable, "-c", "import dagster"], check=False, capture_output=True
    )
    assert not re.search(r"BetaWarning", process.stderr.decode("utf-8"))


def test_no_preview_warnings():
    process = subprocess.run(
        [sys.executable, "-c", "import dagster"], check=False, capture_output=True
    )
    assert not re.search(r"PreviewWarning", process.stderr.decode("utf-8"))


def test_no_supersession_warnings():
    process = subprocess.run(
        [sys.executable, "-c", "import dagster"], check=False, capture_output=True
    )
    assert not re.search(r"SupersessionWarning", process.stderr.decode("utf-8"))


# Fill this with tests for deprecated symbols
def test_deprecated_imports():
    ##### EXAMPLE:
    # with pytest.warns(DeprecationWarning, match=re.escape("Foo is deprecated")):
    #     from dagster import Foo
    pass
