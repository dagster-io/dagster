# pylint: disable=unused-import
from __future__ import absolute_import

from json import dump as dump_, dumps as dumps_

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
