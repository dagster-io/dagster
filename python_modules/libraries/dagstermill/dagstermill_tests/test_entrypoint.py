import runpy
import sys

import pytest


def test_entrypoint():
    argv = list(sys.argv)
    try:
        sys.argv = ["dagstermill", "--help"]
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("dagstermill", run_name="__main__")
        assert exc.value.code == 0
    finally:
        sys.argv = argv
