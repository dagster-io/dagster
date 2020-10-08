"""Test that compute log tail processes go away when the parent hard crashes."""

import sys

from dagster.core.execution.compute_logs import mirror_stream_to_file
from dagster.utils import segfault

if __name__ == "__main__":
    stdout_pids_file, stderr_pids_file = (sys.argv[1], sys.argv[2])
    with mirror_stream_to_file(sys.stdout, stdout_pids_file) as stdout_pids:
        with mirror_stream_to_file(sys.stderr, stderr_pids_file) as stderr_pids:
            sys.stdout.write("stdout pids: {pids}".format(pids=str(stdout_pids)))
            sys.stdout.flush()
            sys.stderr.write("stderr pids: {pids}".format(pids=str(stderr_pids)))
            sys.stderr.flush()
            segfault()
