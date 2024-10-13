# -*- coding: utf-8 -*-
# Vendored from https://github.com/dateutil/dateutil/releases/tag/2.9.0
# Any changes are marked with "# CHANGED IN VENDORED VERSION" (e.g.
# replacing absolute dateutil imports with relative imports)
import sys


# CHANGED IN VENDORED VERSION
__version__ = "2.9.0-vendored"

__all__ = ['easter', 'parser', 'relativedelta', 'rrule', 'tz',
           'utils', 'zoneinfo']

def __getattr__(name):
    import importlib

    if name in __all__:
        return importlib.import_module("." + name, __name__)
    raise AttributeError(
        "module {!r} has not attribute {!r}".format(__name__, name)
    )


def __dir__():
    # __dir__ should include all the lazy-importable modules as well.
    return [x for x in globals() if x not in sys.modules] + __all__
