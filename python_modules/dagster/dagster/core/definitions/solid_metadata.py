from collections import namedtuple

from dagster import check


class SolidMetadata(namedtuple('_SolidMetadata', 'kind hue')):
    def __new__(cls, name, path):
        return super(SolidMetadata, cls).__new__(
            cls, check.str_param(name, 'name'), check.str_param(path, 'path')
        )
