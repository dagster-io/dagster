"""Test interrupt handling."""
import sys
import time

from dagster.utils.interrupts import setup_windows_interrupt_support

if __name__ == "__main__":
    setup_windows_interrupt_support()
    started_sentinel, interrupt_sentinel = (sys.argv[1], sys.argv[2])
    with open(started_sentinel, "w") as fd:
        fd.write("setup_windows_interrupt_support")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        with open(interrupt_sentinel, "w") as fd:
            fd.write("received_keyboard_interrupt")
