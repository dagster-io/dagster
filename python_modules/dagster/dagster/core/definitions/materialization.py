from collections import namedtuple

from dagster import check


class Materialization(namedtuple('_Materialization', 'path description')):
    def __new__(cls, path, description=None):
        return super(Materialization, cls).__new__(
            cls,
            path=check.opt_str_param(path, 'path'),
            description=check.opt_str_param(description, 'description'),
        )
