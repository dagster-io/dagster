# pylint: disable=unused-import
from __future__ import absolute_import

from functools import partial

from yaml import dump as dump_
from yaml import load as load_
from yaml import FullLoader

try:
    from yaml import YAMLError
except ImportError:
    YAMLError = ValueError

dump = dump_

load = partial(load_, Loader=FullLoader)
