from __future__ import absolute_import
from .dauphin import DauphinRegistry

dauphin = DauphinRegistry()


def create_schema():
    # dauphin depends on import-based side effects
    # pylint: disable=W0611
    from dagit.schema import generic, roots, pipelines, execution, runs, errors

    return dauphin.create_schema()
