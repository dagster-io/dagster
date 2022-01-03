import logging
import re
from datetime import datetime
from pathlib import Path
from random import random

import pytest

from consumption_datamart.resources.datawarehouse.base import regexp_extract, utc_timestamp, date_trunc
from consumption_datamart.resources.datawarehouse.sqlite import SQLiteDatawarehouseResource, SQLiteSchema, concat, concat3, concat4


class Test_concat:

    def test_it_should_concat_strings_successfully(self):
        assert concat('one', 'two') == 'onetwo'
        assert concat3('one', 'two', 'three') == 'onetwothree'
        assert concat4('one', 'two', 'three', 'four') == 'onetwothreefour'

    def test_it_should_concat_successfully(self):
        assert concat('one', 2) == 'one2'
        assert concat4('one', 2, 'three', datetime(2021, 10, 1)) == 'one2three2021-10-01 00:00:00'


class Test_regexp_extract:

    def test_it_should_extract_the_first_match_group(self):
        assert regexp_extract('rid:c:fa2c1d78-9f00-4e30-8268-4ab81862080d:attached:attached:gke-01', r'.*:(\S+?)$', 1) == 'gke-01'


# noinspection PyPep8Naming
class Test_utc_timestamp:

    def test_it_should_return_a_utc_timestamp_for_the_current_minute(self):
        assert datetime.utcnow().strftime('%Y-%m-%d %H:%M') in utc_timestamp()

    def test_it_should_return_a_string_in_ISO8601_format(self):
        assert re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+', utc_timestamp())


class Test_date_trunc:

    def test_it_should_truncate_days(self):
        assert date_trunc('day', '2021-05-23 13:21:54') == '2021-05-23'

    def test_it_should_truncate_months(self):
        assert date_trunc('month', '2021-05-23') == '2021-05-01'


@pytest.fixture(scope="class")
def inmemory_dwh():
    base_dir = Path(__file__).parent.parent.parent
    return SQLiteDatawarehouseResource(
        log_manager=logging.getLogger(__name__),
        echo_sql=False,
        schemas=[
            SQLiteSchema(
                'acme_lake', f'file:acme_lake?mode=memory',
                init_sql_file=str((base_dir / "consumption_datamart_tests/test_data/acme_lake.sqlite3.sql").resolve())
            ),
        ],
        pid_group=f"pytest:{random()}"
    )


@pytest.mark.usefixtures("inmemory_dwh")
class Test_SQLiteDatawarehouseResource:

    def test_it_return_data_from_a_sql_statement(self, inmemory_dwh):
        df = inmemory_dwh.read_sql_query("""
            SELECT * 
            FROM acme_lake.invoice_line_items
        """)

        assert len(df) > 0


