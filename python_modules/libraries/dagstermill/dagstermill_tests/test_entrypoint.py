import runpy
import sys

import pytest


def test_entrypoint():
    argv = sys.argv[1:]
    try:
        del sys.argv[1:]
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("dagstermill", run_name="__main__")
        assert exc.value.code == 0
    finally:
        sys.argv += argv
