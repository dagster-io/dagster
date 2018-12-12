from __future__ import absolute_import
from .dauphin import DauphinRegistry

dauphin = DauphinRegistry()


def create_schema():
    from dagit.schema import generic, roots, pipelines, execution, runs, errors
    return dauphin.create_schema()
