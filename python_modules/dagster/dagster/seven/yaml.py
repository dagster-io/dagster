# pylint: disable=unused-import
from __future__ import absolute_import

from yaml import dump as dump_
from yaml import safe_load

try:
    from yaml import YAMLError
except ImportError:
    YAMLError = ValueError

dump = dump_

load = safe_load
