"""Test interrupt handling."""
import sys
import time

from dagster.utils.interrupts import setup_interrupt_handlers

if __name__ == "__main__":
    setup_interrupt_handlers()
    started_sentinel, interrupt_sentinel = (sys.argv[1], sys.argv[2])
    with open(started_sentinel, "w") as fd:
        fd.write("setup_interrupt_handlers")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        with open(interrupt_sentinel, "w") as fd:
            fd.write("received_keyboard_interrupt")
