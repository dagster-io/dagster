import pdb
import sys
import types
from typing import Optional

from dagster._annotations import public


# From https://stackoverflow.com/questions/4716533/how-to-attach-debugger-to-a-python-subproccess
@public
class ForkedPdb(pdb.Pdb):
    """A pdb subclass that may be used from a forked multiprocessing child.

    **Examples**:

    .. code-block:: python

        from dagster._utils.forked_pdb import ForkedPdb

        @solid
        def complex_solid(_):
            # some complicated stuff

            ForkedPdb().set_trace()

            # some other complicated stuff

    You can initiate pipeline execution via the webserver and use the pdb debugger to examine/step through
    execution at the breakpoint.
    """

    def interaction(
        self,
        frame: Optional[types.FrameType],
        traceback: Optional[types.TracebackType],
    ):
        _stdin = sys.stdin
        try:
            sys.stdin = open("/dev/stdin", encoding="utf8")
            pdb.Pdb.interaction(self, frame, traceback)
        finally:
            sys.stdin = _stdin
