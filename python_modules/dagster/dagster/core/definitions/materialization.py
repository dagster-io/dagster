from collections import namedtuple

from dagster import check


class Materialization(namedtuple('_Materialization', 'name path')):
    def __new__(cls, name, path):
        return super(Materialization, cls).__new__(
            cls, check.str_param(name, 'name'), check.str_param(path, 'path')
        )
