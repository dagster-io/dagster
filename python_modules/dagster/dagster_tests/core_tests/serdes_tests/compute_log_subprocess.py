"""Test that compute log tail processes go away when the parent is interrupted using
IPC machinery."""

import sys
import time

from dagster.core.execution.compute_logs import mirror_stream_to_file
from dagster.utils.interrupts import setup_interrupt_handlers

if __name__ == "__main__":
    stdout_filepath, stderr_filepath, opened_sentinel, interrupt_sentinel = (
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
    )
    setup_interrupt_handlers()
    with open(opened_sentinel, "w") as fd:
        fd.write("opened_compute_log_subprocess")
    with mirror_stream_to_file(sys.stdout, stdout_filepath) as stdout_pids:
        with mirror_stream_to_file(sys.stderr, stderr_filepath) as stderr_pids:
            sys.stdout.write("stdout pids: {pids}".format(pids=str(stdout_pids)))
            sys.stdout.flush()
            sys.stderr.write("stderr pids: {pids}".format(pids=str(stderr_pids)))
            sys.stderr.flush()
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                with open(interrupt_sentinel, "w") as fd:
                    fd.write("compute_log_subprocess_interrupt")
