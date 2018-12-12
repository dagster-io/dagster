from __future__ import absolute_import
from .dauphene import DaupheneRegistry

dauphene = DaupheneRegistry()


def create_schema():
    from dagit.schema import generic, roots, pipelines, execution, runs, errors
    return dauphene.create_schema()
