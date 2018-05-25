from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import dagster.core.execution

from dagster.core.execution import (
    execute_pipeline, execute_pipeline_through_solid, output_pipeline
)


def pipeline(**kwargs):
    return dagster.core.execution.DagsterPipeline(**kwargs)


def context(**kwargs):
    return dagster.core.execution.DagsterExecutionContext(**kwargs)


def dep_only_input(solid):
    return dagster.transform_only_solid.dep_only_input(solid)
