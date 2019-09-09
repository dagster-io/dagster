# copied from https://github.com/djrobstep/pgnotify/blob/43bbe7bd3cedfb99700e4ab370cb6f5d7426bea3/pgnotify/notify.py

from __future__ import absolute_import, division, print_function, unicode_literals

import errno
import fcntl
import os
import select
import signal
import sys

from logx import log
from psycopg2.extensions import Notify

from dagster import check

from .utils import get_conn


def get_wakeup_fd():
    pipe_r, pipe_w = os.pipe()
    flags = fcntl.fcntl(pipe_w, fcntl.F_GETFL, 0)
    flags = flags | os.O_NONBLOCK
    flags = fcntl.fcntl(pipe_w, fcntl.F_SETFL, flags)

    signal.set_wakeup_fd(pipe_w)
    return pipe_r


def _empty_handler(_signal, _frame):
    pass


def quote_table_name(name):
    return '"{}"'.format(name)


def start_listening(connection, channels):
    names = (quote_table_name(each) for each in channels)
    listens = '; '.join(['LISTEN {}'.format(n) for n in names])

    with connection.cursor() as curs:
        curs.execute(listens)


def log_notification(notif):
    check.inst_param(notif, 'notif', Notify)
    log.debug('NOTIFY: {}, {}, {}'.format(notif.pid, notif.channel, notif.payload))


def construct_signals(arg):
    # function exists to consolidate and scope pylint directive
    return signal.Signals(arg)  # pylint: disable=no-member


def await_pg_notifications(
    conn_string, channels=None, timeout=5.0, yield_on_timeout=False, handle_signals=None
):
    """Subscribe to PostgreSQL notifications, and handle them
    in infinite-loop style.
    On an actual message, returns the notification (with .pid,
    .channel, and .payload attributes).
    If you've enabled 'yield_on_timeout', yields None on timeout.
    If you've enabled 'handle_keyboardinterrupt', yields False on
    interrupt.
    """

    check.str_param(conn_string, 'conn_string')
    channels = None if channels is None else check.list_param(channels, 'channels', of_type=str)
    check.float_param(timeout, 'timeout')
    check.bool_param(yield_on_timeout, 'yield_on_timeout')

    conn = get_conn(conn_string)

    if channels:
        start_listening(conn, channels)

    signals_to_handle = handle_signals or []
    original_handlers = {}

    try:
        if signals_to_handle:
            original_handlers = {s: signal.signal(s, _empty_handler) for s in signals_to_handle}
            wakeup = get_wakeup_fd()
            listen_on = [conn, wakeup]
        else:
            listen_on = [conn]
            wakeup = None

        while True:
            try:
                r, w, x = select.select(listen_on, [], [], max(0, timeout))
                log.debug('select call awoken, returned: {}'.format((r, w, x)))

                if (r, w, x) == ([], [], []):
                    log.debug('idle timeout on select call, carrying on...')
                    if yield_on_timeout:
                        yield None

                if wakeup is not None and wakeup in r:
                    signal_byte = os.read(wakeup, 1)
                    signal_int = int.from_bytes(signal_byte, sys.byteorder)
                    sig = construct_signals(signal_int)
                    signal_name = construct_signals(sig).name

                    log.info(
                        'woken from slumber by signal: {signal_name}'.format(
                            signal_name=signal_name
                        )
                    )
                    yield signal_int

                if conn in r:
                    conn.poll()

                    notify_list = []
                    while conn.notifies:
                        notify_list.append(conn.notifies.pop())

                    for notif in notify_list:
                        log_notification(notif)
                        yield notif

            except select.error as e:
                e_num, _e_message = e  # pylint: disable=unpacking-non-sequence
                if e_num == errno.EINTR:
                    log.debug('EINTR happened during select')
                else:
                    raise
    finally:
        for s in signals_to_handle or []:
            if s in original_handlers:
                signal_name = construct_signals(s).name
                log.debug(
                    'restoring original handler for: {signal_name}'.format(signal_name=signal_name)
                )
                signal.signal(s, original_handlers[s])
