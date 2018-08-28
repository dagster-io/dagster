import json

from dagster.utils.test import get_temp_file_name
from dagster.utils.logging import (define_json_file_logger, DEBUG, INFO)


def test_basic_logging():
    with get_temp_file_name() as tf_name:
        logger = define_json_file_logger('foo', tf_name, DEBUG)
        logger.debug('bar')

        data = list(parse_json_lines(tf_name))

        assert len(data) == 1
        assert data[0]['name'] == 'foo'
        assert data[0]['msg'] == 'bar'


def parse_json_lines(tf_name):
    with open(tf_name) as f:
        for line in f:
            yield json.loads(line)


def test_no_double_write_diff_names():
    with get_temp_file_name() as tf_name:
        foo_logger = define_json_file_logger('foo', tf_name, DEBUG)
        baaz_logger = define_json_file_logger('baaz', tf_name, DEBUG)

        foo_logger.debug('foo message')
        baaz_logger.debug('baaz message')

        data = list(parse_json_lines(tf_name))

        assert len(data) == 2
        assert data[0]['name'] == 'foo'
        assert data[0]['msg'] == 'foo message'
        assert data[1]['name'] == 'baaz'
        assert data[1]['msg'] == 'baaz message'


# This demonstrates different, less global, behavior than the typical
# python logger. Same name does *not* mean the same logger instance
# here. Hence logger one *retains* debug level while logger_two is
# a separate instance with info level
def test_no_double_write_same_names():
    with get_temp_file_name() as tf_name:
        foo_logger_one = define_json_file_logger('foo', tf_name, DEBUG)
        foo_logger_two = define_json_file_logger('foo', tf_name, INFO)

        foo_logger_one.debug('logger one message')
        foo_logger_two.debug('logger two message')

        data = list(parse_json_lines(tf_name))
        assert len(data) == 1
        assert data[0]['name'] == 'foo'
        assert data[0]['msg'] == 'logger one message'
