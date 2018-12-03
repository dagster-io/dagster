import errno
import os


def mkdir_p(newdir, mode=0o777):
    """The missing mkdir -p functionality in os."""
    try:
        os.makedirs(newdir, mode)
    except OSError as err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(newdir):
            raise
