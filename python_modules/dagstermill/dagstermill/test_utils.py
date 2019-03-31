import sys
from dagstermill import DagstermillError


def notebook_test(f):
    # import this on demand so that main module does not require pytest if this is not called
    import pytest

    # mark this with the "notebook_test" tag so that they can be all be skipped
    # (for performance reasons) and mark them as python3 only

    # In our circleci environment we get periodic and annoying failures
    # where we get this error and its unclear why. We insert a
    # retry here
    def do_test_with_retry():
        try:
            f()
        except DagstermillError as de:
            if 'Kernel died before replying to kernel_info' in str(de):
                f()

    return pytest.mark.notebook_test(
        pytest.mark.skipif(
            sys.version_info < (3, 5),
            reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
        All of the development notebooks currently use the python3 "kernel" so they will
        not be executable in a container that only have python2.7 (e.g. in CircleCI)
        ''',
        )(do_test_with_retry)
    )
