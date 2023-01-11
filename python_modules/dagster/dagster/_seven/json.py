from functools import partial
from json import (
    dump as dump_,
    dumps as dumps_,
    load as load_,
    loads as loads_,
)

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError  # type: ignore[misc, assignment]

dump = partial(dump_, sort_keys=True)

dumps = partial(dumps_, sort_keys=True)

load = partial(load_, strict=False)

loads = partial(loads_, strict=False)
