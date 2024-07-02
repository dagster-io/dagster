from json import (
    dump as dump_,
    load as load_,
    dumps as dumps_,
    loads as loads_,
)
from functools import partial

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

dump = partial(dump_, sort_keys=True)

dumps = partial(dumps_, sort_keys=True)

load = partial(load_, strict=False)

loads = partial(loads_, strict=False)
