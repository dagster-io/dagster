# Utility script for managing compute log stdout mirroring
#
# This script is run as a subprocess during step computation to babysit a tail child process which
# mirrors compute log output from a file to stdout.  This utility script checks to see if its parent
# process has died and kills the tail child process if so.  This is to ensure that execution that
# suddenly exits mid-computation without cleaning up after itself will not orphan long-lived tail
# processes.

import os
import signal
import sys
import time


def watch(args):
    if not args or len(args) != 2:
        return

    parent_pid = int(args[0])
    tail_pid = int(args[1])

    if not parent_pid or not tail_pid:
        return

    while True:
        # check if this process has been orphaned, in which case kill the tail_pid

        # we assume that the process is orphaned if parent pid changes. because systemd
        # user instances also adopt processes, os.getppid() == 1 is no longer a reliable signal
        # for being orphaned.
        if os.getppid() != parent_pid:
            try:
                os.kill(tail_pid, signal.SIGTERM)
            except OSError:
                pass
            break
        else:
            time.sleep(1)


if __name__ == "__main__":
    watch(sys.argv[1:])
