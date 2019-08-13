'''Facilities for running arbitrary commands in child processes.'''

import multiprocessing
import os
import sys
from abc import ABCMeta, abstractmethod
from collections import namedtuple

import six

from dagster import check
from dagster.utils import get_multiprocessing_context
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

ChildProcessStartEvent = namedtuple('ChildProcessStartEvent', 'pid')
ChildProcessDoneEvent = namedtuple('ChildProcessDoneEvent', 'pid')
ChildProcessSystemErrorEvent = namedtuple('ChildProcessSystemErrorEvent', 'pid error_info')

ChildProcessEvents = (ChildProcessStartEvent, ChildProcessDoneEvent, ChildProcessSystemErrorEvent)


class ChildProcessCommand(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''Inherit from this class in order to use this library.
    
    The object must be picklable; instantiate it and pass it to _execute_command_in_child_process.'''

    @abstractmethod
    def execute(self):
        ''' This method is invoked in the child process.
        
        Yields a sequence of events to be handled by _execute_command_in_child_process.'''


class ChildProcessException(Exception):
    '''Thrown when an uncaught exception is raised in the child process.'''

    def __init__(self, *args, **kwargs):
        super(ChildProcessException, self).__init__(*args)
        self.error_info = check.inst_param(
            kwargs.pop('error_info'), 'error_info', SerializableErrorInfo
        )


class ChildProcessCrashException(Exception):
    '''Thrown when the child process crashes.'''


def _execute_command_in_child_process(queue, command):
    '''Wraps the execution of a ChildProcessCommand.
    
    Handles errors and communicates across a queue with the parent process.'''

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


TICK = 20.0 * 1.0 / 1000.0
'''The minimum interval at which to check for child process liveness -- default 20ms.'''

PROCESS_DEAD_AND_QUEUE_EMPTY = 'PROCESS_DEAD_AND_QUEUE_EMPTY'
'''Sentinel value.'''


def _poll_for_event(process, queue):
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
    '''Execute a ChildProcessCommand in a new process.

    This function starts a new process whose execution target is a ChildProcessCommand wrapped by
    _execute_command_in_child_process; polls the queue for events yielded by the child process
    until the process dies and the queue is empty.

    Args:
        command (ChildProcessCommand): The command to execute in the child process.
        return_process_events(Optional[bool]): Set this flag to yield the control events
            (ChildProcessEvents) back to the caller of this function, in addition to any
            non-control events. (default: False)

    Warning: if the child process is in an infinite loop, this will
    also infinitely loop.
    '''

    check.inst_param(command, 'command', ChildProcessCommand)
    check.bool_param(return_process_events, 'return_process_events')

    multiprocessing_context = get_multiprocessing_context()
    queue = multiprocessing_context.Queue()

    process = multiprocessing_context.Process(
        target=_execute_command_in_child_process, args=(queue, command)
    )

    process.start()

    completed_properly = False

    while not completed_properly:
        event = _poll_for_event(process, queue)

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
