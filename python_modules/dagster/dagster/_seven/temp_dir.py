import sys
import tempfile


def get_system_temp_directory():
    if sys.platform == "win32":
        # On windows tempfile.gettempdir() returns the local of the temp
        # directory that should be able to persist between runs
        return tempfile.gettempdir()
    else:
        # On unix variants we use /tmp per convention
        return "/tmp"
