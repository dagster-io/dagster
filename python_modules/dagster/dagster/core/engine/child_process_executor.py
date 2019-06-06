from abc import ABCMeta, abstractmethod
from collections import namedtuple
import multiprocessing
import os
import sys

import six

from dagster import check
from dagster.utils.error import serializable_error_info_from_exc_info, SerializableErrorInfo
from dagster.utils import get_multiprocessing_context


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
    except Exception:  # pylint: disable=broad-except
        queue.put(
            ChildProcessSystemErrorEvent(
                pid=pid, error_info=serializable_error_info_from_exc_info(sys.exc_info())
            )
        )
    finally:
        queue.close()


TICK = 20.0 * 1.0 / 1000.0  # 20 MS

PROCESS_DEAD_AND_QUEUE_EMPTY = 'PROCESS_DEAD_AND_QUEUE_EMPTY'


def get_next_event(process, queue):
    try:
        return queue.get(block=True, timeout=TICK)
    except multiprocessing.queues.Empty:
        if not process.is_alive():
            # There is a possibility that after the last queue.get the
            # process created another event and then died. In that case
            # we want to continue draining the queue.
            try:
                return queue.get(block=False)
            except multiprocessing.queues.Empty:
                # If the queue empty we know that there are no more events
                # and that the process has died.
                return PROCESS_DEAD_AND_QUEUE_EMPTY

    return None


def execute_child_process_command(command, return_process_events=False):
    '''
    This function polls the process until it returns a valid
    item or returns PROCESS_DEAD_AND_QUEUE_EMPTY if it is in
    a state where the process has terminated and the queue is empty.

    If wait_mode is set to YIELD, it will yield None while the process is busy executing.

    Warning: if the child process is in an infinite loop. This will
    also infinitely loop.
    '''

    check.inst_param(command, 'command', ChildProcessCommand)
    check.bool_param(return_process_events, 'return_process_events')

    multiprocessing_context = get_multiprocessing_context()
    queue = multiprocessing_context.Queue()

    process = multiprocessing_context.Process(
        target=execute_command_in_child_process, args=(queue, command)
    )

    process.start()

    completed_properly = False

    while not completed_properly:
        event = get_next_event(process, queue)

        # child process is busy executing, yield so we (the parent) can continue
        # other work such as checking other child_process_commands
        if event is None:
            yield None

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
                'Uncaught exception in process {pid} with message "{message}" and error info {error_info}'.format(
                    pid=event.pid, message=event.error_info.message, error_info=event.error_info
                ),
                error_info=event.error_info,
            )
        elif not isinstance(event, ChildProcessEvents):
            yield event

    if not completed_properly:
        # TODO Gather up stderr and the process exit code
        raise ChildProcessCrashException()

    process.join()
