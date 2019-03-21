# pylint: disable=unused-import
from __future__ import absolute_import

from functools import partial
from json import dump as dump_, dumps as dumps_

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

dump = partial(dump_, sort_keys=True)

dumps = partial(dumps_, sort_keys=True)
