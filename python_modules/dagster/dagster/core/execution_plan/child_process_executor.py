from abc import ABCMeta, abstractmethod
from collections import namedtuple
import multiprocessing
import os
import sys

import six

from dagster import check
from dagster.utils.error import serializable_error_info_from_exc_info, SerializableErrorInfo

ChildProcessStartEvent = namedtuple('ChildProcessStartEvent', 'pid')
ChildProcessDoneEvent = namedtuple('ChildProcessDoneEvent', 'pid')
ChildProcessSystemErrorEvent = namedtuple('ChildProcessSystemErrorEvent', 'pid error_info')

ChildProcessEvents = (ChildProcessStartEvent, ChildProcessDoneEvent, ChildProcessSystemErrorEvent)


# Inherit from this class in order to use this library. The object must be pickable
# and you instantiate it and pass it to execute_command_in_child_process. execute()
# is invoked in a child process
class ChildProcessCommand(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def execute(self):
        pass


class ChildProcessException(Exception):
    def __init__(self, *args, **kwargs):
        super(ChildProcessException, self).__init__(*args)
        self.error_info = check.inst_param(
            kwargs.pop('error_info'), 'error_info', SerializableErrorInfo
        )


def execute_command_in_child_process(queue, command):
    check.inst_param(command, 'command', ChildProcessCommand)

    pid = os.getpid()
    queue.put(ChildProcessStartEvent(pid=pid))
    try:
        for step_event in command.execute():
            queue.put(step_event)
        queue.put(ChildProcessDoneEvent(pid=pid))
    except:  # pylint: disable=bare-except
        queue.put(
            ChildProcessSystemErrorEvent(
                pid=pid, error_info=serializable_error_info_from_exc_info(sys.exc_info())
            )
        )
    finally:
        queue.close()


def execute_child_process_command(command, return_process_events=False):
    check.inst_param(command, 'command', ChildProcessCommand)
    check.bool_param(return_process_events, 'return_process_events')

    queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=execute_command_in_child_process, args=(queue, command)
    )

    process.start()
    while process.is_alive():
        event = queue.get()

        if return_process_events and isinstance(event, ChildProcessEvents):
            yield event

        if isinstance(event, ChildProcessStartEvent):
            continue
        if isinstance(event, ChildProcessDoneEvent):
            break
        if isinstance(event, ChildProcessSystemErrorEvent):
            raise ChildProcessException(
                'Uncaught exception in process {pid} with message "{message}"'.format(
                    pid=event.pid, message=event.error_info.message
                ),
                error_info=event.error_info,
            )

        yield event

    # TODO: Do something reasonable on total process failure
    process.join()
