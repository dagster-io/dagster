# pylint: disable=unused-import
from functools import partial
from json import dump as dump_
from json import dumps as dumps_
from json import load as load_
from json import loads as loads_

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError  # type: ignore[misc, assignment]

dump = partial(dump_, sort_keys=True)

dumps = partial(dumps_, sort_keys=True)

load = partial(load_, strict=False)

loads = partial(loads_, strict=False)
