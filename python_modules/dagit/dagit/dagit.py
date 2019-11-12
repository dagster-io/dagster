#!/usr/bin/env python
import os
import signal
import sys
import time

from watchdog.observers import Observer
from watchdog.tricks import AutoRestartTrick

from dagster import seven

from .cli import ui


# Use watchdog's python API to auto-restart the dagit-cli process when
# python files in the current directory change. This is a slightly modified
# version of the code in watchdog's `watchmedo` CLI. We've modified the
# KeyboardInterrupt handler below to call handler.stop() before tearing
# down the observer so that repeated Ctrl-C's don't cause the process to
# exit and leave dagit-cli dangling.
#
# Original source:
# https://github.com/gorakhargosh/watchdog/blob/master/src/watchdog/watchmedo.py#L124
#
# Issue:
# https://github.com/gorakhargosh/watchdog/issues/543
class DagsterAutoRestartTrick(AutoRestartTrick):
    def __init__(self, *args, **kwargs):
        super(DagsterAutoRestartTrick, self).__init__(*args, **kwargs)
        self.restarting = False

    def on_any_event(self, event):
        self.restarting = True
        super(DagsterAutoRestartTrick, self).on_any_event(event)
        self.restarting = False


def handle_sigterm(_signum, _frame):
    raise KeyboardInterrupt()


# Note: This must be declared outside of `main` or it is cleaned up by
# some weakref magic when the watchmedo restarts Dagit.
host_tempdir = seven.TemporaryDirectory()
watch_tempdir = seven.TemporaryDirectory()


def main():
    # Build the dagit-cli command
    watch_for_reload = True
    fallback_set = False
    command = ['dagit-cli']
    for arg in sys.argv[1:]:
        if arg == '--help':
            watch_for_reload = False
            command.append(arg)
        elif arg == '--version':
            watch_for_reload = False
            command.append(arg)
        elif arg == '--storage-fallback':
            fallback_set = True
            command.append(arg)
        else:
            command.append(arg)

    if not fallback_set:
        command.append('--storage-fallback')
        command.append(host_tempdir.name)

    # Watchdog autorestart doesn't work on Windows because it uses os.setsid
    # See: https://github.com/gorakhargosh/watchdog/issues/387
    if os.name == 'nt':
        watch_for_reload = False

    # If not using watch mode, just call the command.
    if not watch_for_reload:
        ui(command[1:])  # pylint: disable=no-value-for-parameter
        return

    signal.signal(signal.SIGTERM, handle_sigterm)

    # Create a file we'll watch to let Dagit reload itself and pass
    # it explicitly to Dagit to let it know the feature is enabled.
    dagster_reload_trigger = os.path.join(watch_tempdir.name, 'stamp.txt')
    command.append('--reload-trigger')
    command.append(dagster_reload_trigger)

    handler = DagsterAutoRestartTrick(command=command, stop_signal=signal.SIGINT, kill_after=0)
    handler.start()

    observer = Observer(timeout=1)
    observer.schedule(handler, watch_tempdir.name)
    observer.start()

    try:
        while not handler.process or handler.restarting or handler.process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    handler.stop()
    observer.stop()
    observer.join()
