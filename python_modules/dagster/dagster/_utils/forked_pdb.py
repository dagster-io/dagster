import pdb  # noqa: T100
import sys


# From https://stackoverflow.com/questions/4716533/how-to-attach-debugger-to-a-python-subproccess
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

    You can initiate pipeline execution via dagit and use the pdb debugger to examine/step through
    execution at the breakpoint.
    """

    def interaction(self, frame, traceback):
        _stdin = sys.stdin
        try:
            sys.stdin = open("/dev/stdin", encoding="utf8")
            pdb.Pdb.interaction(self, frame, traceback)
        finally:
            sys.stdin = _stdin
