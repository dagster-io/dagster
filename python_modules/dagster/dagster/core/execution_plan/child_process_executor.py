from abc import ABCMeta, abstractmethod
from collections import namedtuple
import multiprocessing
import os
import sys
import time

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


class ChildProcessCrashException(Exception):
    pass


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


def flush_queue(queue):
    events = []
    while not queue.empty():
        events.append(queue.get(block=False))
    return events


TICK = 20.0 * 1.0 / 1000.0

PROCESS_DEAD_AND_QUEUE_EMPTY = 'PROCESS_DEAD_AND_QUEUE_EMPTY'


def get_next_event(process, queue):
    '''
    This function polls the process until it returns a valid
    item or returns PROCESS_DEAD_AND_QUEUE_EMPTY if it is in
    a state where the process has terminated and the queue is empty
    '''
    while True:
        try:
            return queue.get(block=False)
        except multiprocessing.queues.Empty:
            if process.is_alive():
                # processing still going
                # sleep a bit and try to get the item out of the queue again
                time.sleep(TICK)
            else:
                return PROCESS_DEAD_AND_QUEUE_EMPTY

    check.failed('unreachable')


def execute_child_process_command(command, return_process_events=False):
    check.inst_param(command, 'command', ChildProcessCommand)
    check.bool_param(return_process_events, 'return_process_events')

    queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=execute_command_in_child_process, args=(queue, command)
    )

    process.start()

    time.sleep(TICK)

    completed_properly = False

    while not completed_properly:
        event = get_next_event(process, queue)

        if event == PROCESS_DEAD_AND_QUEUE_EMPTY:
            break

        # If we are configured to return process events by the caller,
        # yield that event to the caller
        if return_process_events and isinstance(event, ChildProcessEvents):
            yield event

        if isinstance(event, ChildProcessDoneEvent):
            completed_properly = True
        elif isinstance(event, ChildProcessSystemErrorEvent):
            raise ChildProcessException(
                'Uncaught exception in process {pid} with message "{message}"'.format(
                    pid=event.pid, message=event.error_info.message
                ),
                error_info=event.error_info,
            )
        elif not isinstance(event, ChildProcessEvents):
            yield event

    if not completed_properly:
        # TODO Gather up stderr
        raise ChildProcessCrashException()

    process.join()
