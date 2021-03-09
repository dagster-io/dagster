import errno
from select import error
from threading import Event
from unittest.mock import MagicMock, patch

import pytest
from dagster_postgres.pynotify import await_pg_notifications


def test_await_pg_notifications_failure(conn_string):
    expected_error_num = errno.ECONNREFUSED
    exceptions = [error(errno.EINTR, ""), error(expected_error_num, "")]
    with patch("dagster_postgres.pynotify.select") as mock_select:
        mock_select.select = MagicMock(side_effect=exceptions)
        mock_select.error = error
        with pytest.raises(error) as exc:
            for _ in await_pg_notifications(
                conn_string, channels=["foo"], yield_on_timeout=True, exit_event=Event()
            ):
                pass
        assert exc.value.errno == expected_error_num
