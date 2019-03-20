# pylint: disable=unused-import
from functools import partial
from json import dump as dump_, dumps as dumps_, load, loads, JSONDecoder, JSONEncoder

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

dump = partial(dump_, sort_keys=True)

dumps = partial(dumps_, sort_keys=True)
