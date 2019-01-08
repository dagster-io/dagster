# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_query_execution_plan_snapshot 1'] = {
    'executionPlan': {
        '__typename': 'ExecutionPlan',
        'pipeline': {'name': 'pandas_hello_world'},
        'steps': [
            {
                'inputs': [],
                'name': 'sum_solid.num.input_thunk',
                'outputs': [{'name': 'input_thunk_output', 'type': {'name': 'PandasDataFrame'}}],
                'solid': {'name': 'sum_solid'},
                'tag': 'INPUT_THUNK',
            },
            {
                'inputs': [
                    {
                        'dependsOn': {'name': 'sum_solid.num.input_thunk'},
                        'name': 'num',
                        'type': {'name': 'PandasDataFrame'},
                    }
                ],
                'name': 'sum_solid.transform',
                'outputs': [{'name': 'result', 'type': {'name': 'PandasDataFrame'}}],
                'solid': {'name': 'sum_solid'},
                'tag': 'TRANSFORM',
            },
            {
                'inputs': [
                    {
                        'dependsOn': {'name': 'sum_solid.transform'},
                        'name': 'sum_df',
                        'type': {'name': 'PandasDataFrame'},
                    }
                ],
                'name': 'sum_sq_solid.transform',
                'outputs': [{'name': 'result', 'type': {'name': 'PandasDataFrame'}}],
                'solid': {'name': 'sum_sq_solid'},
                'tag': 'TRANSFORM',
            },
        ],
    }
}
