from functools import partial

from .json_ import dump_, dumps_, JSONDecodeError  # pylint: disable=unused-import

dump = partial(dump_, sort_keys=True)

dumps = partial(dumps_, sort_keys=True)
