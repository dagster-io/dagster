import sys


if sys.version_info < (3, 9):
    from typing_extensions import get_args, get_origin, Annotated
else:
    from typing import get_args, get_origin, Annotated
