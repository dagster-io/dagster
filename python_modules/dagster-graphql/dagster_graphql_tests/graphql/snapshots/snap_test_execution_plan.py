# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_successful_one_part_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'StepMaterializationEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'hydrated_input',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                },
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.inputs.num.read'
                }
            },
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'StepMaterializationEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.transform'
                }
            }
        ]
    }
}
