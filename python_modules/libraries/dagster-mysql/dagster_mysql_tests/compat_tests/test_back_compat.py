# pylint: disable=protected-access

import os
import subprocess
import tempfile

from dagster.core.instance import DagsterInstance
from dagster.utils import datetime_as_float, file_relative_path


def _reconstruct_from_file(hostname, path, username="root", password="test"):
    env = os.environ.copy()
    env["MYSQL_PWD"] = "test"
    subprocess.check_call(f"mysql -uroot -h{hostname} test < {path}", shell=True, env=env)


def test_0_13_17_mysql_convert_float_cols(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        file_relative_path(__file__, "snapshot_0_13_18_start_end_timestamp.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)
        record = instance.get_run_records(limit=1)[0]
        assert record.start_timestamp is None
        assert record.end_timestamp is None

        instance.upgrade()

        record = instance.get_run_records(limit=1)[0]
        assert record.start_timestamp is None
        assert record.end_timestamp is None

        instance.reindex()

        record = instance.get_run_records(limit=1)[0]
        assert int(datetime_as_float(record.start_timestamp)) == 1643788829
        assert int(datetime_as_float(record.end_timestamp)) == 1643788834
