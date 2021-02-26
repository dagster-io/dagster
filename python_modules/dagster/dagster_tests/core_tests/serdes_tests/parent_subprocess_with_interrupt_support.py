"""Test a chain of child processes with interrupt support, ensure that interrupts can be
correctly propagated and handled."""

import sys
import time

from dagster.serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess
from dagster.utils import file_relative_path
from dagster.utils.interrupts import setup_interrupt_handlers

if __name__ == "__main__":
    setup_interrupt_handlers()
    (
        child_opened_sentinel,
        parent_interrupt_sentinel,
        child_started_sentinel,
        child_interrupt_sentinel,
    ) = (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    child_process = open_ipc_subprocess(
        [
            sys.executable,
            file_relative_path(__file__, "subprocess_with_interrupt_support.py"),
            child_started_sentinel,
            child_interrupt_sentinel,
        ]
    )
    with open(child_opened_sentinel, "w") as fd:
        fd.write("opened_ipc_subprocess")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        interrupt_ipc_subprocess(child_process)
        with open(parent_interrupt_sentinel, "w") as fd:
            fd.write("parent_received_keyboard_interrupt")
