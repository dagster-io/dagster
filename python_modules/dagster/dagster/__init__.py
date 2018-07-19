from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import dagster.core.execution

from dagster.core.execution import (
    execute_pipeline, execute_pipeline_through_solid, materialize_pipeline
)

# Note that the structure of this file might end up causing some pretty problematic
# circular dependency issues. Fully qualifying the class names "fixes" issue
# but this is quite fragile -- schrockn (06/04/2018)


def pipeline(**kwargs):
    return dagster.core.execution.DagsterPipeline(**kwargs)


def context(**kwargs):
    return dagster.core.execution.DagsterExecutionContext(**kwargs)


def dep_only_input(solid):
    return dagster.core.definitions.InputDefinition(
        name=solid.name,
        sources=[],
        depends_on=solid,
    )
