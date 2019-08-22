#!/usr/bin/env python
import os
import signal
import sys
import time

from watchdog.observers import Observer
from watchdog.tricks import AutoRestartTrick

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


def main():
    # Build the dagit-cli command, omitting the --no-watch arg if present
    watch = True
    command = ['dagit-cli']
    for arg in sys.argv[1:]:
        if arg == '--no-watch':
            watch = False
        elif arg == '--help':
            watch = False
            command.append(arg)
        elif arg == '--version':
            watch = False
            command.append(arg)
        else:
            command.append(arg)

    # If not using watch mode, just call the command
    if not watch:
        os.execvp(command[0], command)

    signal.signal(signal.SIGTERM, handle_sigterm)

    handler = DagsterAutoRestartTrick(
        command=command,
        patterns=['*.py'],
        ignore_patterns=[],
        ignore_directories=[],
        stop_signal=signal.SIGINT,
        kill_after=0.5,
    )
    handler.start()

    print('Will be watching for file changes...')
    observer = Observer(timeout=1)
    observer.schedule(handler, '.', True)
    observer.start()

    try:
        while not handler.process or handler.restarting or handler.process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    handler.stop()
    observer.stop()
    observer.join()
